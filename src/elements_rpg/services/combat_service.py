"""Combat session management — stateful in-memory combat sessions.

Combat sessions are short-lived (minutes at most), so in-memory storage is
acceptable for the MVP.  Each session is keyed by a UUID and bound to a
single player_id to prevent cross-player access.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

from elements_rpg.combat.manager import CombatManager, CombatResult, CombatRoundResult
from elements_rpg.monsters.bestiary import MVP_SPECIES
from elements_rpg.monsters.models import Monster
from elements_rpg.monsters.skill_catalog import MVP_SKILLS

if TYPE_CHECKING:
    from elements_rpg.skills.progression import Skill

# In-memory combat sessions (acceptable for MVP -- sessions are short-lived)
_active_sessions: dict[str, dict[str, Any]] = {}

# Maximum concurrent sessions per player to prevent abuse
MAX_SESSIONS_PER_PLAYER = 3


class CombatSessionNotFoundError(Exception):
    """Raised when a combat session ID is not found or does not belong to the player."""


class CombatAlreadyFinishedError(Exception):
    """Raised when attempting to execute a round on a finished combat."""


class TooManySessionsError(Exception):
    """Raised when a player exceeds the max concurrent combat sessions."""


def _get_session(session_id: str, player_id: str) -> dict[str, Any]:
    """Retrieve a session, verifying ownership.

    Args:
        session_id: The combat session UUID string.
        player_id: The player UUID string to verify against.

    Returns:
        The session dict.

    Raises:
        CombatSessionNotFoundError: If session is missing or belongs to another player.
    """
    session = _active_sessions.get(session_id)
    if session is None or session["player_id"] != player_id:
        raise CombatSessionNotFoundError(
            f"Combat session '{session_id}' not found for player '{player_id}'"
        )
    return session


def _combat_result_to_dict(result: CombatResult) -> dict[str, Any]:
    """Convert a CombatResult dataclass to a JSON-safe dict."""
    return asdict(result)


def _round_result_to_dict(result: CombatRoundResult) -> dict[str, Any]:
    """Convert a CombatRoundResult dataclass to a JSON-safe dict."""
    return asdict(result)


def _create_enemy_monster(species_id: str, level: int = 1) -> Monster:
    """Create an enemy monster instance from a species ID.

    Args:
        species_id: The species identifier from the bestiary.
        level: The enemy monster's level.

    Returns:
        A fresh Monster instance with full HP and first learnable skill equipped.

    Raises:
        ValueError: If species_id is not in the bestiary.
    """
    species = MVP_SPECIES.get(species_id)
    if species is None:
        raise ValueError(f"Unknown species '{species_id}'. Available: {sorted(MVP_SPECIES.keys())}")

    monster = Monster(
        monster_id=f"enemy_{uuid.uuid4().hex[:8]}",
        species=species,
        level=level,
        experience=0,
        bond_level=0,
        equipped_skill_ids=species.learnable_skill_ids[:1],
        current_hp=species.base_stats.hp,
        is_fainted=False,
    )
    # Set HP to level-scaled value
    monster.current_hp = monster.max_hp()
    return monster


def _build_skill_registry() -> dict[str, Skill]:
    """Build the skill registry from the MVP skill catalog.

    Returns:
        Dict mapping skill_id to Skill instances.
    """
    return dict(MVP_SKILLS)


def _get_combat_state(session: dict[str, Any]) -> dict[str, Any]:
    """Build a snapshot of the current combat state.

    Args:
        session: The session dict from _active_sessions.

    Returns:
        Dict with current combat state suitable for JSON serialization.
    """
    manager: CombatManager = session["manager"]
    return {
        "session_id": session["session_id"],
        "player_id": session["player_id"],
        "round": session["round"],
        "is_finished": manager.is_finished,
        "player_won": manager.player_won,
        "player_team": [
            {
                "monster_id": m.monster_id,
                "species_id": m.species.species_id,
                "name": m.species.name,
                "level": m.level,
                "current_hp": m.current_hp,
                "max_hp": m.max_hp(),
                "is_fainted": m.is_fainted,
            }
            for m in manager.player_team
        ],
        "enemy_team": [
            {
                "monster_id": m.monster_id,
                "species_id": m.species.species_id,
                "name": m.species.name,
                "level": m.level,
                "current_hp": m.current_hp,
                "max_hp": m.max_hp(),
                "is_fainted": m.is_fainted,
            }
            for m in manager.enemy_team
        ],
    }


async def start_combat(
    player_id: str,
    player_monsters: list[Monster],
    enemy_species_ids: list[str],
    enemy_level: int = 1,
) -> dict[str, Any]:
    """Initialize a new combat session.

    Args:
        player_id: The player's UUID string.
        player_monsters: The player's team of monsters for combat.
        enemy_species_ids: List of species IDs to create enemy monsters from.
        enemy_level: Level for enemy monsters (default 1).

    Returns:
        Dict containing session_id and initial combat state.

    Raises:
        ValueError: If player_monsters is empty or enemy_species_ids is empty/invalid.
        TooManySessionsError: If the player has too many active sessions.
    """
    if not player_monsters:
        raise ValueError("Cannot start combat with an empty player team")
    if not enemy_species_ids:
        raise ValueError("Must specify at least one enemy species")

    # Check concurrent session limit
    player_sessions = [s for s in _active_sessions.values() if s["player_id"] == player_id]
    if len(player_sessions) >= MAX_SESSIONS_PER_PLAYER:
        raise TooManySessionsError(
            f"Player '{player_id}' already has {len(player_sessions)} active sessions "
            f"(max {MAX_SESSIONS_PER_PLAYER})"
        )

    enemy_monsters = [_create_enemy_monster(sid, level=enemy_level) for sid in enemy_species_ids]

    session_id = str(uuid.uuid4())
    manager = CombatManager(player_monsters, enemy_monsters)

    session = {
        "session_id": session_id,
        "manager": manager,
        "player_id": player_id,
        "round": 0,
        "skill_registry": _build_skill_registry(),
    }
    _active_sessions[session_id] = session

    return {
        "session_id": session_id,
        "state": _get_combat_state(session),
    }


async def execute_round(session_id: str, player_id: str) -> dict[str, Any]:
    """Execute one combat round.

    Args:
        session_id: The combat session UUID string.
        player_id: The player's UUID string.

    Returns:
        Dict containing round result and updated combat state.

    Raises:
        CombatSessionNotFoundError: If session does not exist or belong to player.
        CombatAlreadyFinishedError: If combat is already over.
    """
    session = _get_session(session_id, player_id)
    manager: CombatManager = session["manager"]

    if manager.is_finished:
        raise CombatAlreadyFinishedError(f"Combat session '{session_id}' is already finished")

    skill_registry = session["skill_registry"]
    round_result = manager.execute_round(skill_registry)
    session["round"] += 1

    return {
        "round_result": _round_result_to_dict(round_result),
        "state": _get_combat_state(session),
    }


async def finish_combat(session_id: str, player_id: str) -> dict[str, Any]:
    """End combat and calculate rewards.

    Removes the session from active sessions and returns the final state.

    Args:
        session_id: The combat session UUID string.
        player_id: The player's UUID string.

    Returns:
        Dict with final combat results (winner, rounds played, combat log).

    Raises:
        CombatSessionNotFoundError: If session does not exist or belong to player.
    """
    # Verify ownership before popping
    _get_session(session_id, player_id)
    session = _active_sessions.pop(session_id)

    manager: CombatManager = session["manager"]

    return {
        "finished": manager.is_finished,
        "player_won": manager.player_won,
        "rounds": session["round"],
        "log": [_round_result_to_dict(r) for r in manager.combat_log],
    }


async def get_combat_state(session_id: str, player_id: str) -> dict[str, Any]:
    """Get current combat state for an active session.

    Args:
        session_id: The combat session UUID string.
        player_id: The player's UUID string.

    Returns:
        Dict with current combat state snapshot.

    Raises:
        CombatSessionNotFoundError: If session does not exist or belong to player.
    """
    session = _get_session(session_id, player_id)
    return _get_combat_state(session)


async def get_combat_log(session_id: str, player_id: str) -> dict[str, Any]:
    """Get combat log for an active session.

    Args:
        session_id: The combat session UUID string.
        player_id: The player's UUID string.

    Returns:
        Dict with session_id, round count, and the full combat log.

    Raises:
        CombatSessionNotFoundError: If session does not exist or belong to player.
    """
    session = _get_session(session_id, player_id)
    manager: CombatManager = session["manager"]

    return {
        "session_id": session_id,
        "rounds": session["round"],
        "log": [_round_result_to_dict(r) for r in manager.combat_log],
    }


def clear_all_sessions() -> None:
    """Remove all active sessions. Used for testing cleanup only."""
    _active_sessions.clear()
