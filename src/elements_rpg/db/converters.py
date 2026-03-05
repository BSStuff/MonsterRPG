"""Bidirectional conversion utilities between Pydantic game models and SQLAlchemy DB models.

The hybrid storage approach uses:
- GameStateDB (JSON column) as the source of truth for save/load
- Relational tables (PlayerDB, MonsterDB, EconomyStateDB) for queryable access

The game_state converters are the most critical path; entity converters
(monster, economy) support the query-optimized relational tables.
"""

from __future__ import annotations

import uuid
from typing import Any

from elements_rpg.db.models.economy import EconomyStateDB
from elements_rpg.db.models.game_state import GameStateDB
from elements_rpg.db.models.monster import MonsterDB
from elements_rpg.db.models.player import PlayerDB
from elements_rpg.economy.manager import EconomyManager
from elements_rpg.monsters.models import Monster  # noqa: TC001 — used at runtime in function bodies
from elements_rpg.player import Player
from elements_rpg.save_load import GameSaveData, load_from_dict, save_to_dict

# ---------------------------------------------------------------------------
# Player converters
# ---------------------------------------------------------------------------


def player_to_db(player: Player, supabase_user_id: str) -> PlayerDB:
    """Convert a Pydantic Player to a SQLAlchemy PlayerDB row.

    Args:
        player: The Pydantic player model.
        supabase_user_id: The Supabase Auth user ID to link.

    Returns:
        A new PlayerDB instance (not yet added to a session).
    """
    return PlayerDB(
        id=uuid.UUID(player.player_id) if _is_uuid(player.player_id) else uuid.uuid4(),
        supabase_user_id=supabase_user_id,
        username=player.username,
        level=player.level,
        experience=player.experience,
    )


def player_from_db(db_player: PlayerDB) -> Player:
    """Convert a SQLAlchemy PlayerDB row to a Pydantic Player.

    Args:
        db_player: The database player row.

    Returns:
        A Pydantic Player model with fields populated from the DB row.
    """
    return Player(
        player_id=str(db_player.id),
        username=db_player.username,
        level=db_player.level,
        experience=db_player.experience,
    )


# ---------------------------------------------------------------------------
# GameState converters (critical path — full save/load)
# ---------------------------------------------------------------------------


def game_state_to_db(save_data: GameSaveData, player_id: uuid.UUID) -> GameStateDB:
    """Convert a Pydantic GameSaveData to a SQLAlchemy GameStateDB row.

    Serializes the full game state as JSON in the save_data column.

    Args:
        save_data: The complete game save data.
        player_id: The player's database UUID.

    Returns:
        A new GameStateDB instance with serialized save data.
    """
    return GameStateDB(
        id=uuid.uuid4(),
        player_id=player_id,
        save_data=save_to_dict(save_data),
        version=save_data.version,
    )


def game_state_from_db(db_state: GameStateDB) -> GameSaveData:
    """Convert a SQLAlchemy GameStateDB row to a Pydantic GameSaveData.

    Deserializes the JSON save_data column back into a full GameSaveData.

    Args:
        db_state: The database game state row.

    Returns:
        A fully populated GameSaveData model.
    """
    return load_from_dict(db_state.save_data)


# ---------------------------------------------------------------------------
# Monster converters (query-optimized relational table)
# ---------------------------------------------------------------------------


def monster_to_db(monster: Monster, player_id: uuid.UUID) -> MonsterDB:
    """Convert a Pydantic Monster to a SQLAlchemy MonsterDB row.

    Extracts key queryable fields into relational columns. The full monster
    state (species, bond details, etc.) lives in the GameStateDB JSON.

    Args:
        monster: The Pydantic monster instance.
        player_id: The owning player's database UUID.

    Returns:
        A new MonsterDB instance.
    """
    return MonsterDB(
        id=uuid.UUID(monster.monster_id) if _is_uuid(monster.monster_id) else uuid.uuid4(),
        player_id=player_id,
        species_id=monster.species.species_id,
        name=monster.species.name,
        level=monster.level,
        experience=monster.experience,
        bond_level=monster.bond_level,
        current_hp=monster.current_hp,
        is_fainted=monster.is_fainted,
        equipped_skill_ids=monster.equipped_skill_ids,
    )


def monster_from_db(db_monster: MonsterDB) -> dict[str, Any]:
    """Extract queryable monster fields from a MonsterDB row.

    Note: This returns a dict of queryable fields, NOT a full Monster instance.
    Full Monster reconstruction requires the species template from the bestiary,
    which is not stored in the relational table. Use game_state_from_db() for
    complete Monster instances.

    Args:
        db_monster: The database monster row.

    Returns:
        A dict with the monster's relational fields.
    """
    return {
        "monster_id": str(db_monster.id),
        "player_id": str(db_monster.player_id),
        "species_id": db_monster.species_id,
        "name": db_monster.name,
        "level": db_monster.level,
        "experience": db_monster.experience,
        "bond_level": db_monster.bond_level,
        "current_hp": db_monster.current_hp,
        "is_fainted": db_monster.is_fainted,
        "equipped_skill_ids": db_monster.equipped_skill_ids,
    }


# ---------------------------------------------------------------------------
# Economy converters (query-optimized relational table)
# ---------------------------------------------------------------------------


def economy_to_db(economy: EconomyManager, player_id: uuid.UUID) -> EconomyStateDB:
    """Convert a Pydantic EconomyManager to a SQLAlchemy EconomyStateDB row.

    Only stores the current balances; transaction history lives in the
    GameStateDB JSON and the transactions ledger table.

    Args:
        economy: The Pydantic economy manager.
        player_id: The owning player's database UUID.

    Returns:
        A new EconomyStateDB instance.
    """
    return EconomyStateDB(
        id=uuid.uuid4(),
        player_id=player_id,
        gold=economy.gold,
        gems=economy.gems,
    )


def economy_from_db(db_economy: EconomyStateDB) -> EconomyManager:
    """Convert a SQLAlchemy EconomyStateDB row to a Pydantic EconomyManager.

    Restores the gold/gems balances. Transaction history is NOT restored
    from this table — use game_state_from_db() for the full state including
    transaction logs.

    Args:
        db_economy: The database economy state row.

    Returns:
        An EconomyManager with balances set (no transaction history).
    """
    return EconomyManager(
        gold=db_economy.gold,
        gems=db_economy.gems,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False
