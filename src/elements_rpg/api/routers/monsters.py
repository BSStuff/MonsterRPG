"""Monsters router -- bestiary, owned monsters, and monster management endpoints.

Client-trusted XP/bond endpoints have been removed. XP and bond are only
awarded through validated server-side actions (combat completion, taming, etc.).
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.dependencies import resolve_player_id
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services import monster_service

router = APIRouter(prefix="/monsters", tags=["Monsters"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class UpdateSkillsRequest(BaseModel):
    """Request body for updating equipped skills."""

    skill_ids: list[str] = Field(
        max_length=4,
        description="Skill IDs to equip (max 4)",
    )


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------


@router.get("/bestiary")
async def get_bestiary() -> SuccessResponse[list[dict[str, Any]]]:
    """List all available monster species from the bestiary."""
    species_list = await monster_service.get_bestiary()
    return SuccessResponse(
        data=[s.model_dump() for s in species_list],
    )


@router.get("/bestiary/{species_id}")
async def get_species(species_id: str) -> SuccessResponse[dict[str, Any]]:
    """Get details for a specific monster species."""
    species = await monster_service.get_species(species_id)
    if species is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Species '{species_id}' not found in bestiary",
        )
    return SuccessResponse(data=species.model_dump())


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.get("/owned")
async def get_owned_monsters(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[list[dict[str, Any]]]:
    """List all monsters owned by the authenticated player."""
    player_id = await resolve_player_id(db, user)
    monsters = await monster_service.get_owned_monsters(db, player_id)
    return SuccessResponse(data=monsters)


@router.get("/{monster_id}")
async def get_monster(
    monster_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Get details of a specific owned monster."""
    player_id = await resolve_player_id(db, user)
    monster_uuid = _parse_uuid(monster_id, "monster_id")
    monster = await monster_service.get_monster(db, player_id, monster_uuid)
    if monster is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Monster '{monster_id}' not found or not owned by you",
        )
    return SuccessResponse(data=monster)


@router.put("/{monster_id}/skills")
async def update_skills(
    monster_id: str,
    body: UpdateSkillsRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Update equipped skills on a monster (max 4)."""
    player_id = await resolve_player_id(db, user)
    monster_uuid = _parse_uuid(monster_id, "monster_id")
    try:
        result = await monster_service.update_skills(db, player_id, monster_uuid, body.skill_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    """Parse a string as UUID, raising 400 if invalid."""
    try:
        return uuid.UUID(value)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID for {field_name}: '{value}'",
        ) from e
