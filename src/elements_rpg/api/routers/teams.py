"""Teams router -- team management and composition endpoints."""

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
from elements_rpg.services import team_service

router = APIRouter(prefix="/teams", tags=["Teams"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class CreateTeamRequest(BaseModel):
    """Request body for creating a team."""

    name: str = Field(
        default="Team 1",
        min_length=1,
        max_length=30,
        description="Display name for the team",
    )
    monster_ids: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="Monster UUIDs to add (max 6)",
    )
    roles: dict[str, str] | None = Field(
        default=None,
        description="Optional monster_id -> role mapping",
    )


class UpdateTeamRequest(BaseModel):
    """Request body for updating a team."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
        description="New team name (optional)",
    )
    monster_ids: list[str] | None = Field(
        default=None,
        max_length=6,
        description="New monster UUIDs (optional, replaces all)",
    )
    roles: dict[str, str] | None = Field(
        default=None,
        description="Optional monster_id -> role mapping",
    )


class ReorderTeamRequest(BaseModel):
    """Request body for reordering team members."""

    ordered_monster_ids: list[str] = Field(
        description="Monster UUIDs in desired order",
    )


class AssignRolesRequest(BaseModel):
    """Request body for assigning roles."""

    role_assignments: dict[str, str] = Field(
        description="Mapping of monster_id -> role",
    )


def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    """Parse a string as UUID, raising 400 if invalid."""
    try:
        return uuid.UUID(value)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID for {field_name}: '{value}'",
        ) from e


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/")
async def list_teams(
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[list[dict[str, Any]]]:
    """List all teams for the authenticated player."""
    player_id = await resolve_player_id(db, user)
    teams = await team_service.get_teams(db, player_id)
    return SuccessResponse(data=teams)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_team(
    body: CreateTeamRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Create a new team (up to 6 monsters)."""
    player_id = await resolve_player_id(db, user)
    try:
        team = await team_service.create_team(
            db,
            player_id,
            body.name,
            body.monster_ids,
            body.roles,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=team)


@router.put("/{team_id}")
async def update_team(
    team_id: str,
    body: UpdateTeamRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Update a team's name and/or composition."""
    player_id = await resolve_player_id(db, user)
    team_uuid = _parse_uuid(team_id, "team_id")
    try:
        team = await team_service.update_team(
            db,
            player_id,
            team_uuid,
            name=body.name,
            monster_ids=body.monster_ids,
            roles=body.roles,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=team)


@router.delete("/{team_id}")
async def delete_team(
    team_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, str]]:
    """Delete a team."""
    player_id = await resolve_player_id(db, user)
    team_uuid = _parse_uuid(team_id, "team_id")
    try:
        await team_service.delete_team(db, player_id, team_uuid)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data={"deleted": team_id})


@router.put("/{team_id}/reorder")
async def reorder_team(
    team_id: str,
    body: ReorderTeamRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Reorder members within a team."""
    player_id = await resolve_player_id(db, user)
    team_uuid = _parse_uuid(team_id, "team_id")
    try:
        team = await team_service.reorder_team(
            db,
            player_id,
            team_uuid,
            body.ordered_monster_ids,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=team)


@router.put("/{team_id}/roles")
async def assign_roles(
    team_id: str,
    body: AssignRolesRequest,
    db: AsyncSession = Depends(get_db),
    user: dict[str, Any] = Depends(get_current_user),
) -> SuccessResponse[dict[str, Any]]:
    """Assign roles to team members."""
    player_id = await resolve_player_id(db, user)
    team_uuid = _parse_uuid(team_id, "team_id")
    try:
        team = await team_service.assign_roles(
            db,
            player_id,
            team_uuid,
            body.role_assignments,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=team)
