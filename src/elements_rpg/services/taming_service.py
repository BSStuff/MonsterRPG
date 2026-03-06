"""Taming service — bridges taming logic with DB persistence.

Loads the taming tracker from the player's game state, performs taming
operations using the core taming module, and persists updated state back.
When taming succeeds, creates a new MonsterDB row for the player.
"""

from __future__ import annotations

import random
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.db.models.monster import MonsterDB
from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.monsters.taming import (
    BASE_CAPTURE_RATES,
    attempt_tame,
    calculate_pity_bonus,
    calculate_tame_chance,
)
from elements_rpg.services.save_service import load_game_state, save_game_state


async def calculate_chance(
    db: AsyncSession,
    player_id: uuid.UUID,
    species_id: str,
    food_bonus: float = 0.0,
    skill_bonus: float = 0.0,
) -> dict[str, Any]:
    """Calculate the taming chance for a species without attempting.

    Loads the player's taming tracker to include pity bonus in the calculation.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        species_id: The species to calculate chance for.
        food_bonus: Bonus from food item (0.0-1.0).
        skill_bonus: Bonus from player taming skill (0.0-1.0).

    Returns:
        Dict with base_rate, food_bonus, skill_bonus, pity_bonus, final_chance.

    Raises:
        ValueError: If species_id is not in the bestiary or no game save exists.
    """
    species = MVP_SPECIES.get(species_id)
    if species is None:
        raise ValueError(f"Unknown species: '{species_id}'. Not found in bestiary.")

    game_state = await load_game_state(db, player_id)
    if game_state is None:
        raise ValueError(f"No game save found for player {player_id}. Create a save first.")

    tracker = game_state.taming_tracker
    attempts = tracker.get_attempts(species_id)
    pity_bonus = calculate_pity_bonus(attempts)
    base_rate = BASE_CAPTURE_RATES.get(species.rarity, 0.10)

    final_chance = calculate_tame_chance(
        rarity=species.rarity,
        food_bonus=food_bonus,
        skill_bonus=skill_bonus,
        pity_bonus=pity_bonus,
    )

    return {
        "species_id": species_id,
        "base_rate": base_rate,
        "food_bonus": food_bonus,
        "skill_bonus": skill_bonus,
        "pity_bonus": pity_bonus,
        "attempts": attempts,
        "final_chance": final_chance,
    }


async def attempt_tame_monster(
    db: AsyncSession,
    player_id: uuid.UUID,
    species_id: str,
    food_bonus: float = 0.0,
    skill_bonus: float = 0.0,
) -> dict[str, Any]:
    """Attempt to tame a monster, persisting the result.

    On success, creates a new MonsterDB row for the player and resets pity.
    On failure, increments the pity counter in the game state.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        species_id: The species to attempt taming.
        food_bonus: Bonus from food item (0.0-1.0).
        skill_bonus: Bonus from player taming skill (0.0-1.0).

    Returns:
        Dict with success, attempt details, and new monster data if caught.

    Raises:
        ValueError: If species_id is not in the bestiary or no game save exists.
    """
    species = MVP_SPECIES.get(species_id)
    if species is None:
        raise ValueError(f"Unknown species: '{species_id}'. Not found in bestiary.")

    game_state = await load_game_state(db, player_id)
    if game_state is None:
        raise ValueError(f"No game save found for player {player_id}. Create a save first.")

    tracker = game_state.taming_tracker
    roll = random.random()  # noqa: S311 — game mechanic, not security

    result = attempt_tame(
        rarity=species.rarity,
        species_id=species_id,
        tracker=tracker,
        roll=roll,
        food_bonus=food_bonus,
        skill_bonus=skill_bonus,
    )

    response: dict[str, Any] = {
        "success": result.success,
        "attempt_number": result.attempt_number,
        "base_rate": result.base_rate,
        "food_bonus": result.food_bonus,
        "skill_bonus": result.skill_bonus,
        "pity_bonus": result.pity_bonus,
        "final_chance": result.final_chance,
        "monster": None,
    }

    if result.success:
        monster_row = await _create_tamed_monster(db, player_id, species_id)
        response["monster"] = {
            "monster_id": str(monster_row.id),
            "species_id": monster_row.species_id,
            "name": monster_row.name,
            "level": monster_row.level,
            "species": {
                "name": species.name,
                "element": species.element.value,
                "rarity": species.rarity.value,
            },
        }

    # Persist updated taming tracker in game state
    await save_game_state(db, player_id, game_state)

    return response


async def get_tracker(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the player's taming pity tracker state.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.

    Returns:
        Dict mapping species_id to {attempts, pity_bonus}.

    Raises:
        ValueError: If no game save exists for the player.
    """
    game_state = await load_game_state(db, player_id)
    if game_state is None:
        raise ValueError(f"No game save found for player {player_id}. Create a save first.")

    tracker = game_state.taming_tracker
    result: dict[str, Any] = {}

    for species_id, attempts in tracker.attempts_per_species.items():
        result[species_id] = {
            "attempts": attempts,
            "pity_bonus": calculate_pity_bonus(attempts),
        }

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _create_tamed_monster(
    db: AsyncSession,
    player_id: uuid.UUID,
    species_id: str,
) -> MonsterDB:
    """Create a new MonsterDB row for a successfully tamed monster.

    The monster starts at level 1 with full HP from the species base stats.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        species_id: The species that was tamed.

    Returns:
        The newly created MonsterDB row.
    """
    species = MVP_SPECIES[species_id]
    monster_row = MonsterDB(
        id=uuid.uuid4(),
        player_id=player_id,
        species_id=species_id,
        name=species.name,
        level=1,
        experience=0,
        bond_level=0,
        current_hp=species.base_stats.hp,
        is_fainted=False,
        equipped_skill_ids=[],
    )
    db.add(monster_row)
    await db.flush()
    return monster_row
