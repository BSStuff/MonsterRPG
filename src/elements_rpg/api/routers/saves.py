"""Save/Load router — game save CRUD endpoints.

All endpoints require Supabase JWT authentication.  The player's internal
UUID is resolved from the JWT ``sub`` claim via the players table.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.dependencies import resolve_player_id
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.save_load import GameSaveData  # noqa: TC001 — used at runtime as request body
from elements_rpg.services.save_service import (
    create_fresh_save,
    get_save_version,
    load_game_state,
    save_game_state,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/saves", tags=["Save/Load"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class SaveRequest(BaseModel):
    """Request body for saving game state with optional optimistic locking."""

    save_data: GameSaveData
    expected_version: int | None = Field(
        default=None,
        description="Expected current save version for optimistic locking. "
        "If provided and does not match, save will be rejected with 409.",
    )


class SaveConfirmation(BaseModel):
    """Response returned after a successful save."""

    success: bool = True
    version: int
    timestamp: str


class SaveVersionInfo(BaseModel):
    """Lightweight metadata about the player's save."""

    version: int
    updated_at: str | None = None
    exists: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/", response_model=SaveConfirmation, status_code=200)
async def create_save(
    body: SaveRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SaveConfirmation:
    """Save current game state for the authenticated player.

    Accepts a full GameSaveData JSON body with optional expected_version
    for optimistic locking. If expected_version is provided and does not
    match the current version, returns 409 Conflict.
    """
    player_id = await resolve_player_id(db, current_user)
    try:
        db_state = await save_game_state(
            db, player_id, body.save_data, expected_version=body.expected_version
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    updated_at = db_state.updated_at
    timestamp = updated_at.isoformat() if updated_at else ""
    return SaveConfirmation(
        success=True,
        version=db_state.version,
        timestamp=timestamp,
    )


@router.get("/", response_model=SuccessResponse[dict[str, Any]], status_code=200)
async def load_save(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Load current game state for the authenticated player.

    Returns the full GameSaveData as JSON inside a SuccessResponse wrapper.
    """
    player_id = await resolve_player_id(db, current_user)
    game_data = await load_game_state(db, player_id)
    if game_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No save found for this player.",
        )
    return SuccessResponse(data=game_data.model_dump())


@router.post("/new", response_model=SuccessResponse[dict[str, Any]], status_code=201)
async def create_new_save_endpoint(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Create a fresh save for the authenticated player.

    Returns 409 Conflict if the player already has a save.
    """
    player_id = await resolve_player_id(db, current_user)

    # Derive username from JWT email or fallback
    username = current_user.get("email", "Player")

    try:
        game_data = await create_fresh_save(db, player_id, username)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return SuccessResponse(data=game_data.model_dump())


@router.get("/version", response_model=SaveVersionInfo, status_code=200)
async def get_save_version_endpoint(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SaveVersionInfo:
    """Get save metadata (version and timestamp) without loading full data."""
    player_id = await resolve_player_id(db, current_user)
    info = await get_save_version(db, player_id)
    return SaveVersionInfo(**info)
