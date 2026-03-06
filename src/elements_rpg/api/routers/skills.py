"""Skills router -- skill catalog, progression, and strategy management endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services import skills_service
from elements_rpg.services.player_service import get_player_by_supabase_id

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/skills", tags=["Skills & Strategy"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class GrantXPRequest(BaseModel):
    """Request body for granting XP."""

    amount: int = Field(gt=0, description="XP to grant (must be positive)")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_player_id(
    db: AsyncSession,
    current_user: dict[str, Any],
) -> Any:
    """Resolve internal player UUID from JWT sub claim."""
    supabase_uid: str = current_user["sub"]
    player = await get_player_by_supabase_id(db, supabase_uid)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No player profile found for this account. Register first.",
        )
    return player.id


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------


@router.get("/catalog")
async def get_skill_catalog() -> SuccessResponse[list[dict[str, Any]]]:
    """List all available skills in the catalog."""
    catalog = skills_service.get_skill_catalog()
    return SuccessResponse(data=catalog)


@router.get("/strategies")
async def list_strategies() -> SuccessResponse[list[dict[str, Any]]]:
    """List all strategy profiles and proficiency levels."""
    strategies = skills_service.get_strategies()
    return SuccessResponse(data=strategies)


@router.get("/{skill_id}")
async def get_skill(skill_id: str) -> SuccessResponse[dict[str, Any]]:
    """Get details of a specific skill including level and milestones."""
    skill = skills_service.get_skill(skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Skill '{skill_id}' not found in catalog",
        )
    return SuccessResponse(data=skill)


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.post("/{skill_id}/experience")
async def grant_skill_experience(
    skill_id: str,
    body: GrantXPRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Grant experience to a skill from usage."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await skills_service.grant_skill_xp(db, player_id, skill_id, body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)


@router.post("/strategies/{strategy}/experience")
async def grant_strategy_experience(
    strategy: str,
    body: GrantXPRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Grant experience to a strategy profile."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await skills_service.grant_strategy_xp(db, player_id, strategy, body.amount)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return SuccessResponse(data=result)
