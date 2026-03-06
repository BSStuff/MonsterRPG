"""Skills router -- skill catalog and strategy information endpoints (read-only).

Client-trusted XP endpoints have been removed. Skill and strategy XP are only
awarded through validated server-side actions (combat completion, etc.).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, status

from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.services import skills_service

router = APIRouter(prefix="/skills", tags=["Skills & Strategy"])


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
