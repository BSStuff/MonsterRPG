"""Combat router — combat session management and execution endpoints.

All endpoints require Supabase JWT authentication.  Combat sessions are
stored in-memory (not DB) since they are short-lived.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.monsters.models import Monster
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


def _create_placeholder_team() -> list[Monster]:
    """Create a placeholder player team for MVP testing.

    In production, this would load the player's active team from the DB.
    For now, creates a team from the first 3 species in the bestiary.
    """
    species_list = list(MVP_SPECIES.values())[:3]
    team: list[Monster] = []
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
        team.append(monster)
    return team


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/start", response_model=SuccessResponse[dict[str, Any]], status_code=201)
async def start_combat_endpoint(
    body: StartCombatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Start a new combat session.

    Accepts a list of enemy species IDs and creates a combat session.
    For MVP, uses a placeholder player team.

    Returns session_id and initial combat state.
    """
    player_id = _get_player_id(current_user)

    # Validate species IDs
    invalid_ids = [sid for sid in body.enemy_species_ids if sid not in MVP_SPECIES]
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown species IDs: {invalid_ids}. Available: {sorted(MVP_SPECIES.keys())}",
        )

    # TODO: Load player's actual team from DB when team service is implemented
    player_team = _create_placeholder_team()

    try:
        result = await start_combat(
            player_id=player_id,
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
) -> SuccessResponse[dict[str, Any]]:
    """End a combat session and calculate rewards.

    Removes the session from active sessions and returns the final combat
    results including winner, round count, and full combat log.
    """
    player_id = _get_player_id(current_user)

    try:
        result = await finish_combat(session_id, player_id)
    except CombatSessionNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

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
