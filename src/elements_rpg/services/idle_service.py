"""Idle, offline gains, and action queue operations with DB persistence.

Loads the player's GameSaveData, applies idle/queue mutations via the
existing Pydantic models, then persists changes back through save_service.
"""

from __future__ import annotations

import uuid  # noqa: TC003 -- used at runtime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.economy.action_queue import ActionQueue, QueuedAction  # noqa: TC001
from elements_rpg.idle.offline_gains import OfflineGainsResult
from elements_rpg.idle.offline_gains import calculate_offline_gains as _calc_offline
from elements_rpg.idle.tracker import AreaClearRecord, IdleTracker
from elements_rpg.services.save_service import load_game_state, save_game_state


async def _load_state(db: AsyncSession, player_id: uuid.UUID) -> Any:
    """Load game state or raise ValueError if missing."""
    state = await load_game_state(db, player_id)
    if state is None:
        raise ValueError(f"No save found for player {player_id}")
    return state


# ---------------------------------------------------------------------------
# Idle tracker
# ---------------------------------------------------------------------------


async def record_clear(
    db: AsyncSession,
    player_id: uuid.UUID,
    area_id: str,
    clear_time_seconds: float,
    monsters_defeated: int,
    timestamp: float = 0.0,
) -> dict[str, Any]:
    """Record an area clear and update the player's idle tracker.

    Args:
        db: Async database session.
        player_id: Player's internal UUID.
        area_id: The area that was cleared.
        clear_time_seconds: Time taken to clear the area.
        monsters_defeated: Number of monsters defeated.
        timestamp: Unix timestamp of the clear.

    Returns:
        Dict with is_new_best flag and current BRPM/idle_rate for the area.
    """
    state = await _load_state(db, player_id)
    record = AreaClearRecord(
        area_id=area_id,
        clear_time_seconds=clear_time_seconds,
        monsters_defeated=monsters_defeated,
        timestamp=timestamp,
    )
    is_new_best = state.idle_tracker.record_clear(record)
    await save_game_state(db, player_id, state)
    return {
        "area_id": area_id,
        "is_new_best": is_new_best,
        "brpm": state.idle_tracker.get_brpm(area_id),
        "idle_rate": state.idle_tracker.get_idle_rate(area_id),
        "best_clear_time": state.idle_tracker.best_clear_times.get(area_id),
    }


async def get_tracker(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the player's idle tracker with BRPM data for all areas.

    Returns:
        Dict with per-area BRPM, idle_rate, and best clear times.
    """
    state = await _load_state(db, player_id)
    tracker: IdleTracker = state.idle_tracker
    areas: dict[str, Any] = {}
    for area_id in tracker.best_clear_times:
        areas[area_id] = {
            "best_clear_time": tracker.best_clear_times[area_id],
            "best_monsters_per_clear": tracker.best_monsters_per_clear.get(area_id, 0),
            "brpm": tracker.get_brpm(area_id),
            "idle_rate": tracker.get_idle_rate(area_id),
            "idle_monsters_per_minute": tracker.get_idle_monsters_per_minute(area_id),
        }
    return {"areas": areas}


async def calculate_offline_gains(
    db: AsyncSession,
    player_id: uuid.UUID,
    area_id: str,
    hours_offline: float,
) -> OfflineGainsResult:
    """Calculate offline gains for the player without applying them.

    Args:
        db: Async database session.
        player_id: Player's internal UUID.
        area_id: The area the player was idling in.
        hours_offline: Duration offline in hours.

    Returns:
        OfflineGainsResult with estimated rewards.
    """
    state = await _load_state(db, player_id)
    return _calc_offline(state.idle_tracker, area_id, hours_offline)


# ---------------------------------------------------------------------------
# Action queue
# ---------------------------------------------------------------------------


async def get_action_queue(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the player's current action queue state.

    Returns:
        Dict with queue slots, active count, and action list.
    """
    state = await _load_state(db, player_id)
    queue: ActionQueue = state.action_queue
    return {
        "max_slots": queue.max_slots,
        "active_count": queue.active_count,
        "has_free_slot": queue.has_free_slot,
        "actions": [a.model_dump() for a in queue.actions],
    }


async def add_action(
    db: AsyncSession,
    player_id: uuid.UUID,
    action: QueuedAction,
) -> dict[str, Any]:
    """Add an action to the player's queue.

    Args:
        db: Async database session.
        player_id: Player's internal UUID.
        action: The action to add.

    Returns:
        Updated queue state.

    Raises:
        ValueError: If the queue is full.
    """
    state = await _load_state(db, player_id)
    added = state.action_queue.add_action(action)
    if not added:
        raise ValueError(
            f"Action queue is full ({state.action_queue.max_slots} slots). "
            "Cancel an action or expand your queue."
        )
    await save_game_state(db, player_id, state)
    return {
        "added": True,
        "action": action.model_dump(),
        "max_slots": state.action_queue.max_slots,
        "active_count": state.action_queue.active_count,
    }


async def cancel_action(
    db: AsyncSession,
    player_id: uuid.UUID,
    action_id: str,
) -> dict[str, Any]:
    """Cancel a queued action.

    Args:
        db: Async database session.
        player_id: Player's internal UUID.
        action_id: The ID of the action to cancel.

    Returns:
        Dict with cancellation result.

    Raises:
        ValueError: If action not found or already complete.
    """
    state = await _load_state(db, player_id)
    cancelled = state.action_queue.cancel_action(action_id)
    if not cancelled:
        raise ValueError(f"Action '{action_id}' not found or already completed/cancelled.")
    await save_game_state(db, player_id, state)
    return {"cancelled": True, "action_id": action_id}


async def advance_queue(
    db: AsyncSession,
    player_id: uuid.UUID,
    seconds: float,
) -> dict[str, Any]:
    """Advance all in-progress actions by given seconds.

    Args:
        db: Async database session.
        player_id: Player's internal UUID.
        seconds: Time to advance in seconds.

    Returns:
        Dict with completed actions and updated queue state.
    """
    if seconds <= 0:
        raise ValueError(f"Seconds must be positive, got {seconds}")

    state = await _load_state(db, player_id)
    completed = state.action_queue.advance_all(seconds)
    await save_game_state(db, player_id, state)
    return {
        "advanced_seconds": seconds,
        "completed_actions": [a.model_dump() for a in completed],
        "completed_count": len(completed),
        "active_count": state.action_queue.active_count,
    }


async def expand_queue(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Expand the player's action queue by one slot.

    Args:
        db: Async database session.
        player_id: Player's internal UUID.

    Returns:
        Dict with new max_slots value.

    Raises:
        ValueError: If already at max slots (8).
    """
    state = await _load_state(db, player_id)
    queue: ActionQueue = state.action_queue
    old_slots = queue.max_slots
    if old_slots >= 8:
        raise ValueError("Action queue is already at maximum capacity (8 slots).")
    new_max = queue.expand_slots(1)
    await save_game_state(db, player_id, state)
    return {
        "previous_slots": old_slots,
        "new_slots": new_max,
    }
