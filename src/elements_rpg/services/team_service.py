"""Team CRUD operations with DB persistence.

Provides async functions for creating, reading, updating, deleting, reordering,
and assigning roles to teams. Bridges between the Pydantic Team model and
SQLAlchemy TeamDB/TeamMemberDB persistence.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.config import MAX_TEAM_SIZE
from elements_rpg.db.models.monster import MonsterDB
from elements_rpg.db.models.team import TeamDB, TeamMemberDB


async def get_teams(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Get all teams owned by a player, including members.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.

    Returns:
        List of team dicts, each with a 'members' list.
    """
    result = await db.execute(
        select(TeamDB).where(TeamDB.player_id == player_id).order_by(TeamDB.created_at)
    )
    rows = result.scalars().all()
    teams = []
    for row in rows:
        team_data = await _build_team_response(db, row)
        teams.append(team_data)
    return teams


async def get_team(
    db: AsyncSession,
    player_id: uuid.UUID,
    team_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Get a single team, verifying ownership.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        team_id: The team's UUID.

    Returns:
        Team dict with members if found and owned, None otherwise.
    """
    row = await _get_owned_team_row(db, player_id, team_id)
    if row is None:
        return None
    return await _build_team_response(db, row)


async def create_team(
    db: AsyncSession,
    player_id: uuid.UUID,
    name: str,
    monster_ids: list[str],
    roles: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create a new team with members.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        name: Display name for the team.
        monster_ids: List of monster UUIDs to add (max 6).
        roles: Optional mapping of monster_id -> role string.

    Returns:
        The newly created team dict with members.

    Raises:
        ValueError: If validation fails (too many monsters, duplicates,
            unowned monsters).
    """
    roles = roles or {}
    _validate_monster_count(monster_ids)
    _validate_no_duplicates(monster_ids)
    await _validate_ownership(db, player_id, monster_ids)

    team = TeamDB(
        id=uuid.uuid4(),
        player_id=player_id,
        name=name,
    )
    db.add(team)
    await db.flush()

    for position, mid_str in enumerate(monster_ids):
        member = TeamMemberDB(
            id=uuid.uuid4(),
            team_id=team.id,
            monster_id=uuid.UUID(mid_str),
            role=roles.get(mid_str),
            position=position,
        )
        db.add(member)

    await db.flush()
    return await _build_team_response(db, team)


async def update_team(
    db: AsyncSession,
    player_id: uuid.UUID,
    team_id: uuid.UUID,
    name: str | None = None,
    monster_ids: list[str] | None = None,
    roles: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Update a team's name and/or composition.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        team_id: The team's UUID.
        name: New team name (optional).
        monster_ids: New list of monster UUIDs (optional, replaces all members).
        roles: Optional mapping of monster_id -> role string.

    Returns:
        Updated team dict with members.

    Raises:
        ValueError: If team not found/not owned or validation fails.
    """
    row = await _get_owned_team_row(db, player_id, team_id)
    if row is None:
        raise ValueError(f"Team {team_id} not found or not owned by player {player_id}")

    if name is not None:
        row.name = name

    if monster_ids is not None:
        roles = roles or {}
        _validate_monster_count(monster_ids)
        _validate_no_duplicates(monster_ids)
        await _validate_ownership(db, player_id, monster_ids)

        # Delete existing members
        await db.execute(delete(TeamMemberDB).where(TeamMemberDB.team_id == team_id))

        # Insert new members
        for position, mid_str in enumerate(monster_ids):
            member = TeamMemberDB(
                id=uuid.uuid4(),
                team_id=team_id,
                monster_id=uuid.UUID(mid_str),
                role=roles.get(mid_str),
                position=position,
            )
            db.add(member)

    await db.flush()
    return await _build_team_response(db, row)


async def delete_team(
    db: AsyncSession,
    player_id: uuid.UUID,
    team_id: uuid.UUID,
) -> bool:
    """Delete a team, verifying ownership.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        team_id: The team's UUID.

    Returns:
        True if the team was deleted.

    Raises:
        ValueError: If team not found or not owned.
    """
    row = await _get_owned_team_row(db, player_id, team_id)
    if row is None:
        raise ValueError(f"Team {team_id} not found or not owned by player {player_id}")

    await db.execute(delete(TeamMemberDB).where(TeamMemberDB.team_id == team_id))
    await db.execute(delete(TeamDB).where(TeamDB.id == team_id))
    await db.flush()
    return True


async def reorder_team(
    db: AsyncSession,
    player_id: uuid.UUID,
    team_id: uuid.UUID,
    ordered_monster_ids: list[str],
) -> dict[str, Any]:
    """Reorder members within a team.

    The provided monster IDs must exactly match the current team members.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        team_id: The team's UUID.
        ordered_monster_ids: Monster IDs in the new desired order.

    Returns:
        Updated team dict with reordered members.

    Raises:
        ValueError: If team not found/not owned or IDs don't match.
    """
    row = await _get_owned_team_row(db, player_id, team_id)
    if row is None:
        raise ValueError(f"Team {team_id} not found or not owned by player {player_id}")

    members = await _get_team_members(db, team_id)
    current_ids = sorted(str(m.monster_id) for m in members)
    requested_ids = sorted(ordered_monster_ids)

    if current_ids != requested_ids:
        raise ValueError(
            "Reorder IDs must exactly match current team members. "
            f"Current: {current_ids}, Requested: {requested_ids}"
        )

    member_by_monster = {str(m.monster_id): m for m in members}
    for position, mid_str in enumerate(ordered_monster_ids):
        member_by_monster[mid_str].position = position

    await db.flush()
    return await _build_team_response(db, row)


async def assign_roles(
    db: AsyncSession,
    player_id: uuid.UUID,
    team_id: uuid.UUID,
    role_assignments: dict[str, str],
) -> dict[str, Any]:
    """Assign roles to team members.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        team_id: The team's UUID.
        role_assignments: Mapping of monster_id (str) -> role (str).

    Returns:
        Updated team dict with roles applied.

    Raises:
        ValueError: If team not found/not owned or monster not on team.
    """
    row = await _get_owned_team_row(db, player_id, team_id)
    if row is None:
        raise ValueError(f"Team {team_id} not found or not owned by player {player_id}")

    members = await _get_team_members(db, team_id)
    member_by_monster = {str(m.monster_id): m for m in members}

    for mid_str, role in role_assignments.items():
        if mid_str not in member_by_monster:
            raise ValueError(
                f"Monster {mid_str} is not on team {team_id}. "
                f"Team members: {list(member_by_monster.keys())}"
            )
        member_by_monster[mid_str].role = role

    await db.flush()
    return await _build_team_response(db, row)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_owned_team_row(
    db: AsyncSession,
    player_id: uuid.UUID,
    team_id: uuid.UUID,
) -> TeamDB | None:
    """Fetch a TeamDB row verifying ownership."""
    result = await db.execute(
        select(TeamDB).where(
            TeamDB.id == team_id,
            TeamDB.player_id == player_id,
        )
    )
    return result.scalar_one_or_none()


async def _get_team_members(
    db: AsyncSession,
    team_id: uuid.UUID,
) -> list[TeamMemberDB]:
    """Fetch all members of a team, ordered by position."""
    result = await db.execute(
        select(TeamMemberDB).where(TeamMemberDB.team_id == team_id).order_by(TeamMemberDB.position)
    )
    return list(result.scalars().all())


async def _build_team_response(
    db: AsyncSession,
    row: TeamDB,
) -> dict[str, Any]:
    """Build a team response dict including members."""
    members = await _get_team_members(db, row.id)
    return {
        "team_id": str(row.id),
        "player_id": str(row.player_id),
        "name": row.name,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "members": [
            {
                "member_id": str(m.id),
                "monster_id": str(m.monster_id),
                "role": m.role,
                "position": m.position,
            }
            for m in members
        ],
    }


def _validate_monster_count(monster_ids: list[str]) -> None:
    """Ensure the list does not exceed MAX_TEAM_SIZE."""
    if len(monster_ids) > MAX_TEAM_SIZE:
        raise ValueError(f"Team cannot exceed {MAX_TEAM_SIZE} monsters, got {len(monster_ids)}")


def _validate_no_duplicates(monster_ids: list[str]) -> None:
    """Ensure no duplicate monster IDs."""
    if len(monster_ids) != len(set(monster_ids)):
        raise ValueError("Team cannot contain duplicate monster IDs")


async def _validate_ownership(
    db: AsyncSession,
    player_id: uuid.UUID,
    monster_ids: list[str],
) -> None:
    """Verify all monster IDs are owned by the player.

    Raises:
        ValueError: If any monster is not owned by the player.
    """
    if not monster_ids:
        return

    monster_uuids = [uuid.UUID(mid) for mid in monster_ids]
    result = await db.execute(
        select(MonsterDB.id).where(
            MonsterDB.id.in_(monster_uuids),
            MonsterDB.player_id == player_id,
        )
    )
    found_ids = {str(row) for row in result.scalars().all()}
    missing = [mid for mid in monster_ids if mid not in found_ids]
    if missing:
        raise ValueError(f"Monsters not owned by player {player_id}: {missing}")
