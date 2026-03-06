"""Monster operations with DB persistence.

Provides async functions for querying the bestiary, managing owned monsters,
granting XP/bond, and updating equipped skills. Bridges between the
Pydantic Monster model logic and SQLAlchemy MonsterDB persistence.
"""

from __future__ import annotations

import uuid  # noqa: TC003 — used at runtime for uuid.UUID() calls
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.config import MAX_EQUIPPED_SKILLS
from elements_rpg.db.models.monster import MonsterDB
from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.monsters.models import Monster, MonsterSpecies


async def get_bestiary() -> list[MonsterSpecies]:
    """Return all available monster species from the bestiary.

    Returns:
        List of all MonsterSpecies defined in the MVP bestiary.
    """
    return list(MVP_SPECIES.values())


async def get_species(species_id: str) -> MonsterSpecies | None:
    """Get a single species by ID.

    Args:
        species_id: The species identifier to look up.

    Returns:
        The MonsterSpecies if found, None otherwise.
    """
    return MVP_SPECIES.get(species_id)


async def get_owned_monsters(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Get all monsters owned by a player.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.

    Returns:
        List of monster data dicts enriched with species info.
    """
    result = await db.execute(select(MonsterDB).where(MonsterDB.player_id == player_id))
    rows = result.scalars().all()
    return [_enrich_monster_row(row) for row in rows]


async def get_monster(
    db: AsyncSession,
    player_id: uuid.UUID,
    monster_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Get a specific monster, verifying ownership.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        monster_id: The monster's UUID.

    Returns:
        Enriched monster data dict if found and owned, None otherwise.
    """
    result = await db.execute(
        select(MonsterDB).where(
            MonsterDB.id == monster_id,
            MonsterDB.player_id == player_id,
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return _enrich_monster_row(row)


async def grant_xp(
    db: AsyncSession,
    player_id: uuid.UUID,
    monster_id: uuid.UUID,
    xp_amount: int,
) -> dict[str, Any]:
    """Grant XP to a monster, handling level-ups.

    Loads the monster from DB, reconstructs the Pydantic Monster to use
    gain_experience() logic, then persists the updated stats.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        monster_id: The monster's UUID.
        xp_amount: Amount of XP to grant (must be >= 0).

    Returns:
        Dict with updated monster data and level_up info.

    Raises:
        ValueError: If xp_amount is negative or monster not found/not owned.
    """
    if xp_amount < 0:
        raise ValueError(f"XP amount must be non-negative, got {xp_amount}")

    row = await _get_owned_monster_row(db, player_id, monster_id)
    if row is None:
        raise ValueError(f"Monster {monster_id} not found or not owned by player {player_id}")

    monster = _row_to_monster(row)
    old_level = monster.level
    levels_gained = monster.gain_experience(xp_amount)

    row.level = monster.level
    row.experience = monster.experience
    await db.flush()

    enriched = _enrich_monster_row(row)
    enriched["level_up"] = {
        "previous_level": old_level,
        "new_level": monster.level,
        "levels_gained": levels_gained,
    }
    return enriched


async def increase_bond(
    db: AsyncSession,
    player_id: uuid.UUID,
    monster_id: uuid.UUID,
    amount: int,
) -> dict[str, Any]:
    """Increase a monster's bond level.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        monster_id: The monster's UUID.
        amount: Bond points to add (must be >= 0).

    Returns:
        Dict with updated monster data and bond change info.

    Raises:
        ValueError: If amount is negative or monster not found/not owned.
    """
    if amount < 0:
        raise ValueError(f"Bond amount must be non-negative, got {amount}")

    row = await _get_owned_monster_row(db, player_id, monster_id)
    if row is None:
        raise ValueError(f"Monster {monster_id} not found or not owned by player {player_id}")

    monster = _row_to_monster(row)
    old_bond = monster.bond_level
    new_bond = monster.gain_bond(amount)

    row.bond_level = new_bond
    await db.flush()

    enriched = _enrich_monster_row(row)
    enriched["bond_change"] = {
        "previous_bond": old_bond,
        "new_bond": new_bond,
    }
    return enriched


async def update_skills(
    db: AsyncSession,
    player_id: uuid.UUID,
    monster_id: uuid.UUID,
    skill_ids: list[str],
) -> dict[str, Any]:
    """Update a monster's equipped skills.

    Validates that:
    - At most MAX_EQUIPPED_SKILLS (4) skills are provided.
    - No duplicate skill IDs.
    - All skills are learnable by this monster's species.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        monster_id: The monster's UUID.
        skill_ids: List of skill IDs to equip (max 4).

    Returns:
        Dict with updated monster data.

    Raises:
        ValueError: If validation fails or monster not found/not owned.
    """
    if len(skill_ids) > MAX_EQUIPPED_SKILLS:
        raise ValueError(
            f"Cannot equip more than {MAX_EQUIPPED_SKILLS} skills, got {len(skill_ids)}"
        )

    if len(skill_ids) != len(set(skill_ids)):
        raise ValueError("Duplicate skill IDs are not allowed")

    row = await _get_owned_monster_row(db, player_id, monster_id)
    if row is None:
        raise ValueError(f"Monster {monster_id} not found or not owned by player {player_id}")

    species = MVP_SPECIES.get(row.species_id)
    if species is None:
        raise ValueError(f"Unknown species: {row.species_id}")

    invalid_skills = [sid for sid in skill_ids if sid not in species.learnable_skill_ids]
    if invalid_skills:
        raise ValueError(
            f"Skills not learnable by {species.name}: {invalid_skills}. "
            f"Learnable: {species.learnable_skill_ids}"
        )

    row.equipped_skill_ids = skill_ids
    await db.flush()

    return _enrich_monster_row(row)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _get_owned_monster_row(
    db: AsyncSession,
    player_id: uuid.UUID,
    monster_id: uuid.UUID,
) -> MonsterDB | None:
    """Fetch a MonsterDB row verifying ownership."""
    result = await db.execute(
        select(MonsterDB).where(
            MonsterDB.id == monster_id,
            MonsterDB.player_id == player_id,
        )
    )
    return result.scalar_one_or_none()


def _row_to_monster(row: MonsterDB) -> Monster:
    """Reconstruct a Pydantic Monster from a MonsterDB row.

    Requires the species to exist in the bestiary.

    Raises:
        ValueError: If species_id is not in the bestiary.
    """
    species = MVP_SPECIES.get(row.species_id)
    if species is None:
        raise ValueError(f"Unknown species in DB: {row.species_id}")

    return Monster(
        monster_id=str(row.id),
        species=species,
        level=row.level,
        experience=row.experience,
        bond_level=row.bond_level,
        equipped_skill_ids=row.equipped_skill_ids or [],
        current_hp=row.current_hp,
        is_fainted=row.is_fainted,
    )


def _enrich_monster_row(row: MonsterDB) -> dict[str, Any]:
    """Convert a MonsterDB row to a response dict with species info.

    Adds species details (name, element, rarity, base_stats, passive)
    from the bestiary if the species is known.
    """
    species = MVP_SPECIES.get(row.species_id)
    data: dict[str, Any] = {
        "monster_id": str(row.id),
        "player_id": str(row.player_id),
        "species_id": row.species_id,
        "name": row.name,
        "level": row.level,
        "experience": row.experience,
        "bond_level": row.bond_level,
        "current_hp": row.current_hp,
        "is_fainted": row.is_fainted,
        "equipped_skill_ids": row.equipped_skill_ids or [],
    }
    if species is not None:
        types_list = [species.primary_type.value]
        if species.secondary_type is not None:
            types_list.append(species.secondary_type.value)
        data["species"] = {
            "name": species.name,
            "types": types_list,
            "element": species.element.value,  # backward compat (primary type)
            "rarity": species.rarity.value,
            "base_stats": species.base_stats.model_dump(),
            "passive_trait": species.passive_trait,
            "passive_description": species.passive_description,
            "learnable_skill_ids": species.learnable_skill_ids,
        }
    return data
