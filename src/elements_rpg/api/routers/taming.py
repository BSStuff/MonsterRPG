"""Taming router -- taming chance calculation, attempts, and pity tracking."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services import player_service, taming_service

router = APIRouter(prefix="/taming", tags=["Taming"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CalculateChanceRequest(BaseModel):
    """Request body for taming chance calculation."""

    species_id: str = Field(min_length=1, description="Species to calculate chance for")
    food_bonus: float = Field(default=0.0, ge=0.0, le=1.0, description="Bonus from food item")
    skill_bonus: float = Field(default=0.0, ge=0.0, le=1.0, description="Bonus from taming skill")


class AttemptTameRequest(BaseModel):
    """Request body for a taming attempt."""

    species_id: str = Field(min_length=1, description="Species to attempt taming")
    food_bonus: float = Field(default=0.0, ge=0.0, le=1.0, description="Bonus from food item")
    skill_bonus: float = Field(default=0.0, ge=0.0, le=1.0, description="Bonus from taming skill")


# ---------------------------------------------------------------------------
# Helper: resolve player_id from JWT
# ---------------------------------------------------------------------------


async def _resolve_player_id(
    db: AsyncSession,
    user: dict[str, Any],
) -> uuid.UUID:
    """Look up the internal player ID from Supabase user ID.

    Raises:
        HTTPException 404: If no player record exists for this user.
    """
    supabase_user_id = user["sub"]
    player = await player_service.get_player_by_supabase_id(db, supabase_user_id)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found. Register first.",
        )
    return player.id


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/calculate")
async def calculate_taming_chance(
    body: CalculateChanceRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Calculate the current taming chance for a species (includes pity bonus)."""
    player_id = await _resolve_player_id(db, user)
    try:
        result = await taming_service.calculate_chance(
            db,
            player_id,
            species_id=body.species_id,
            food_bonus=body.food_bonus,
            skill_bonus=body.skill_bonus,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.post("/attempt")
async def attempt_taming(
    body: AttemptTameRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Attempt to tame a monster. Returns success/fail and updated pity state."""
    player_id = await _resolve_player_id(db, user)
    try:
        result = await taming_service.attempt_tame_monster(
            db,
            player_id,
            species_id=body.species_id,
            food_bonus=body.food_bonus,
            skill_bonus=body.skill_bonus,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.get("/tracker")
async def get_taming_tracker(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Get current pity counters for all species."""
    player_id = await _resolve_player_id(db, user)
    try:
        result = await taming_service.get_tracker(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)
