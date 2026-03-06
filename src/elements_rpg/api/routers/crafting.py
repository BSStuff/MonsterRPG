"""Crafting router — recipes, crafting execution, inventory, and life skills endpoints.

Client-trusted life-skill XP endpoint has been removed. Life skill XP is only
awarded through validated server-side actions (crafting completion, action queue).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.dependencies import resolve_player_id
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

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/crafting", tags=["Crafting & Life Skills"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CraftRequest(BaseModel):
    """Request body for executing a crafting recipe."""

    recipe_id: str = Field(min_length=1, description="The recipe ID to craft")


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
    """Craft an item -- checks materials, deducts, and produces result.

    Life skill XP is automatically awarded on successful crafting.
    """
    player_id = await resolve_player_id(db, current_user)
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
    player_id = await resolve_player_id(db, current_user)
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
    """List all life skills with levels and XP (read-only)."""
    player_id = await resolve_player_id(db, current_user)
    try:
        skills = await service_get_life_skills(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=skills)
