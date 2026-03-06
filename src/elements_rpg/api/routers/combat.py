"""Combat router — combat session management and execution endpoints.

All endpoints require Supabase JWT authentication. Combat sessions are
stored in-memory (not DB) since they are short-lived.

The finish endpoint awards XP and gold server-side based on enemies defeated.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.dependencies import resolve_player_id
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.services import monster_service
from elements_rpg.services.combat_service import (
    CombatAlreadyFinishedError,
    CombatSessionNotFoundError,
    TooManySessionsError,
    execute_round,
    finish_combat,
    get_combat_log,
    get_combat_state,
    start_combat,
)
from elements_rpg.services.economy_service import earn_gold

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/combat", tags=["Combat"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class StartCombatRequest(BaseModel):
    """Request body for starting a new combat session.

    Attributes:
        enemy_species_ids: List of species IDs to fight against.
        enemy_level: Level for enemy monsters (default 1).
    """

    enemy_species_ids: list[str] = Field(
        min_length=1,
        max_length=6,
        description="List of enemy species IDs (1-6 enemies)",
    )
    enemy_level: int = Field(
        default=1,
        ge=1,
        le=100,
        description="Level of enemy monsters",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_player_id(current_user: dict[str, Any]) -> str:
    """Extract player ID from JWT payload."""
    return current_user["sub"]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", response_model=SuccessResponse[dict[str, Any]], status_code=201)
async def start_combat_endpoint(
    body: StartCombatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Start a new combat session.

    Loads the player's actual monsters from DB and creates a combat session.
    Returns session_id and initial combat state.
    """
    player_id_str = _get_player_id(current_user)
    player_id = await resolve_player_id(db, current_user)

    # Validate species IDs
    invalid_ids = [sid for sid in body.enemy_species_ids if sid not in MVP_SPECIES]
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown species IDs: {invalid_ids}. Available: {sorted(MVP_SPECIES.keys())}",
        )

    # Load player's actual monsters from DB
    owned_monsters = await monster_service.get_owned_monsters(db, player_id)
    if not owned_monsters:
        # Fallback: create a basic team from bestiary for players with no monsters yet
        from elements_rpg.monsters.models import Monster

        species_list = list(MVP_SPECIES.values())[:3]
        player_team = []
        for i, species in enumerate(species_list):
            monster = Monster(
                monster_id=f"player_mon_{i}",
                species=species,
                level=5,
                experience=0,
                bond_level=10,
                equipped_skill_ids=species.learnable_skill_ids[:2],
                current_hp=species.base_stats.hp,
                is_fainted=False,
            )
            monster.current_hp = monster.max_hp()
            player_team.append(monster)
    else:
        # Convert DB monster dicts to Monster instances
        from elements_rpg.monsters.models import Monster

        player_team = []
        for mon_data in owned_monsters[:6]:
            species = MVP_SPECIES.get(mon_data.get("species_id", ""))
            if species is None:
                continue
            monster = Monster(
                monster_id=mon_data.get("monster_id", f"mon_{len(player_team)}"),
                species=species,
                level=mon_data.get("level", 1),
                experience=mon_data.get("experience", 0),
                bond_level=mon_data.get("bond_level", 0),
                equipped_skill_ids=mon_data.get("equipped_skill_ids", [])
                or species.learnable_skill_ids[:2],
                current_hp=mon_data.get("current_hp", species.base_stats.hp),
                is_fainted=mon_data.get("is_fainted", False),
            )
            monster.current_hp = monster.max_hp()
            player_team.append(monster)

        if not player_team:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid monsters found in your collection.",
            )

    try:
        result = await start_combat(
            player_id=player_id_str,
            player_monsters=player_team,
            enemy_species_ids=body.enemy_species_ids,
            enemy_level=body.enemy_level,
        )
    except TooManySessionsError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return SuccessResponse(data=result)


@router.post(
    "/{session_id}/round",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=200,
)
async def process_round(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Process one combat round and return results.

    Executes all monster actions in speed order for the current round.
    """
    player_id = _get_player_id(current_user)

    try:
        result = await execute_round(session_id, player_id)
    except CombatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except CombatAlreadyFinishedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return SuccessResponse(data=result)


@router.post(
    "/{session_id}/finish",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=200,
)
async def finish_combat_endpoint(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """End a combat session, calculate rewards, and persist them.

    If the player won, awards XP to participating monsters and gold to
    the player's economy -- all server-authoritative.
    """
    player_id_str = _get_player_id(current_user)

    try:
        result = await finish_combat(session_id, player_id_str)
    except CombatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    # Persist rewards server-side if player won
    rewards = result.get("rewards", {})
    if rewards.get("gold_earned", 0) > 0:
        try:
            player_id = await resolve_player_id(db, current_user)
            await earn_gold(db, player_id, rewards["gold_earned"], "combat_reward")
        except (ValueError, HTTPException):
            pass  # Don't fail the response if reward persistence fails

    return SuccessResponse(data=result)


@router.get(
    "/{session_id}",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=200,
)
async def get_combat_session(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Get the current state of a combat session."""
    player_id = _get_player_id(current_user)

    try:
        result = await get_combat_state(session_id, player_id)
    except CombatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return SuccessResponse(data=result)


@router.get(
    "/{session_id}/log",
    response_model=SuccessResponse[dict[str, Any]],
    status_code=200,
)
async def get_combat_log_endpoint(
    session_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Get the combat log for a session."""
    player_id = _get_player_id(current_user)

    try:
        result = await get_combat_log(session_id, player_id)
    except CombatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return SuccessResponse(data=result)
