"""Crafting router — recipes, crafting execution, inventory, and life skills endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services.crafting_service import (
    execute_craft_recipe,
)
from elements_rpg.services.crafting_service import (
    get_inventory as service_get_inventory,
)
from elements_rpg.services.crafting_service import (
    get_life_skills as service_get_life_skills,
)
from elements_rpg.services.crafting_service import (
    get_recipes as service_get_recipes,
)
from elements_rpg.services.crafting_service import (
    grant_life_skill_xp as service_grant_xp,
)
from elements_rpg.services.player_service import get_player_by_supabase_id

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/crafting", tags=["Crafting & Life Skills"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CraftRequest(BaseModel):
    """Request body for executing a crafting recipe."""

    recipe_id: str = Field(min_length=1, description="The recipe ID to craft")


class GrantXPRequest(BaseModel):
    """Request body for granting life skill XP."""

    amount: int = Field(gt=0, description="XP amount to grant")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_player_id(
    db: AsyncSession,
    current_user: dict[str, Any],
) -> Any:
    """Resolve the internal player UUID from the JWT sub claim."""
    supabase_uid: str = current_user["sub"]
    player = await get_player_by_supabase_id(db, supabase_uid)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No player profile found for this account. Register first.",
        )
    return player.id


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------


@router.get("/recipes")
async def list_recipes() -> SuccessResponse[list[dict[str, Any]]]:
    """List all available crafting recipes."""
    recipes = await service_get_recipes()
    return SuccessResponse(data=recipes)


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.post("/execute")
async def execute_craft(
    body: CraftRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Craft an item -- checks materials, deducts, and produces result."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await execute_craft_recipe(db, player_id, body.recipe_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.get("/inventory")
async def get_inventory(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Get the player's material inventory."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        inventory = await service_get_inventory(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=inventory)


@router.get("/life-skills")
async def list_life_skills(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[list[dict[str, Any]]]:
    """List all life skills with levels and XP."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        skills = await service_get_life_skills(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=skills)


@router.post("/life-skills/{skill_id}/experience")
async def grant_life_skill_experience(
    skill_id: str,
    body: GrantXPRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Grant experience to a life skill."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_grant_xp(db, player_id, skill_id, body.amount)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)
