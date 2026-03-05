"""Player CRUD operations against PostgreSQL.

Provides async functions for creating, reading, and updating player profiles.
Bridges the Supabase Auth user ID to internal player records and initializes
fresh game saves on registration.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002 — used at runtime as parameter type

from elements_rpg.db.models.game_state import GameStateDB
from elements_rpg.db.models.player import PlayerDB
from elements_rpg.save_load import create_new_save, save_to_dict


async def create_player(
    db: AsyncSession,
    supabase_user_id: str,
    username: str,
) -> PlayerDB:
    """Create a new player with a fresh game save.

    Creates both the PlayerDB row and an initial GameStateDB row containing
    a fresh save (3 life skills at level 1, empty inventory, etc.).

    Args:
        db: The async database session.
        supabase_user_id: The Supabase Auth user ID.
        username: The player's display name.

    Returns:
        The newly created PlayerDB instance (flushed, ID available).

    Raises:
        sqlalchemy.exc.IntegrityError: If supabase_user_id or username
            violates a unique constraint.
    """
    player = PlayerDB(
        id=uuid.uuid4(),
        supabase_user_id=supabase_user_id,
        username=username,
        level=1,
        experience=0,
    )
    db.add(player)
    await db.flush()

    # Create initial game state
    save_data = create_new_save(str(player.id), username)
    game_state = GameStateDB(
        id=uuid.uuid4(),
        player_id=player.id,
        save_data=save_to_dict(save_data),
        version=save_data.version,
    )
    db.add(game_state)

    return player


async def get_player_by_supabase_id(
    db: AsyncSession,
    supabase_user_id: str,
) -> PlayerDB | None:
    """Find a player by their Supabase auth user ID.

    Args:
        db: The async database session.
        supabase_user_id: The Supabase Auth user ID to look up.

    Returns:
        The PlayerDB instance if found, None otherwise.
    """
    result = await db.execute(select(PlayerDB).where(PlayerDB.supabase_user_id == supabase_user_id))
    return result.scalar_one_or_none()


async def get_player_by_id(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> PlayerDB | None:
    """Find a player by their internal player ID.

    Args:
        db: The async database session.
        player_id: The internal UUID of the player.

    Returns:
        The PlayerDB instance if found, None otherwise.
    """
    result = await db.execute(select(PlayerDB).where(PlayerDB.id == player_id))
    return result.scalar_one_or_none()


async def update_player(
    db: AsyncSession,
    player: PlayerDB,
    **updates: Any,
) -> PlayerDB:
    """Update player fields.

    Only updates attributes that exist on the PlayerDB model.
    Flushes changes to the session (caller controls commit/rollback).

    Args:
        db: The async database session.
        player: The PlayerDB instance to update.
        **updates: Key-value pairs of fields to update.

    Returns:
        The updated PlayerDB instance.

    Raises:
        ValueError: If no valid fields are provided in updates.
    """
    valid_fields = {"username", "level", "experience"}
    applied = 0
    for key, value in updates.items():
        if key in valid_fields and hasattr(player, key):
            setattr(player, key, value)
            applied += 1

    if applied == 0 and updates:
        invalid_keys = set(updates.keys()) - valid_fields
        raise ValueError(
            f"No valid update fields provided. Invalid keys: {invalid_keys}. "
            f"Allowed fields: {valid_fields}"
        )

    await db.flush()
    return player
