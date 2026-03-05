"""Save/load operations for game state persistence.

Provides async CRUD functions that bridge GameSaveData (Pydantic) with
GameStateDB (SQLAlchemy) via the converters module.  All functions take
an async DB session and a player UUID — the caller (router) is responsible
for extracting those from the JWT / dependency injection.
"""

from __future__ import annotations

import uuid  # noqa: TC003 — used at runtime in function bodies
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from elements_rpg.db.converters import game_state_from_db, game_state_to_db
from elements_rpg.db.models.game_state import GameStateDB
from elements_rpg.save_load import GameSaveData, create_new_save, save_to_dict

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def save_game_state(
    db: AsyncSession,
    player_id: uuid.UUID,
    save_data: GameSaveData,
) -> GameStateDB:
    """Save full game state — upsert into game_states table.

    If an existing save exists for the player, updates the save_data JSON
    and increments the version.  Otherwise creates a new row.

    Args:
        db: The async database session.
        player_id: The player's database UUID.
        save_data: The complete game save data to persist.

    Returns:
        The persisted GameStateDB row (new or updated).
    """
    result = await db.execute(select(GameStateDB).where(GameStateDB.player_id == player_id))
    existing = result.scalar_one_or_none()

    if existing is not None:
        existing.save_data = save_to_dict(save_data)
        existing.version = existing.version + 1
        await db.flush()
        return existing

    new_state = game_state_to_db(save_data, player_id)
    db.add(new_state)
    await db.flush()
    return new_state


async def load_game_state(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> GameSaveData | None:
    """Load latest game state for player.

    Args:
        db: The async database session.
        player_id: The player's database UUID.

    Returns:
        The deserialized GameSaveData if a save exists, None otherwise.
    """
    result = await db.execute(select(GameStateDB).where(GameStateDB.player_id == player_id))
    db_state = result.scalar_one_or_none()
    if db_state is None:
        return None
    return game_state_from_db(db_state)


async def get_save_version(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict:
    """Get save version and timestamp without loading full data.

    Args:
        db: The async database session.
        player_id: The player's database UUID.

    Returns:
        A dict with version, updated_at, and exists fields.
    """
    result = await db.execute(
        select(GameStateDB.version, GameStateDB.updated_at).where(
            GameStateDB.player_id == player_id
        )
    )
    row = result.one_or_none()

    if row is None:
        return {"version": 0, "updated_at": None, "exists": False}

    version, updated_at = row
    return {
        "version": version,
        "updated_at": updated_at.isoformat() if updated_at else datetime.now(UTC).isoformat(),
        "exists": True,
    }


async def create_fresh_save(
    db: AsyncSession,
    player_id: uuid.UUID,
    username: str,
) -> GameSaveData:
    """Create a brand new save for a player and persist it.

    Args:
        db: The async database session.
        player_id: The player's database UUID.
        username: The player's display name for the new save.

    Returns:
        The freshly created GameSaveData.

    Raises:
        ValueError: If the player already has a save.
    """
    result = await db.execute(select(GameStateDB.id).where(GameStateDB.player_id == player_id))
    if result.scalar_one_or_none() is not None:
        raise ValueError(f"Player {player_id} already has a save. Cannot create a fresh one.")

    save_data = create_new_save(str(player_id), username)
    new_state = game_state_to_db(save_data, player_id)
    db.add(new_state)
    await db.flush()
    return save_data
