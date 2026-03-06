"""Economy service — currency operations and area queries via game state persistence.

Bridges between API routers and the EconomyManager / Area models.
All currency mutations follow the pattern: load game state -> modify -> save back.
"""

from __future__ import annotations

import uuid  # noqa: TC003 — used at runtime in function signatures
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.economy.areas import MVP_AREAS
from elements_rpg.services.save_service import load_game_state, save_game_state

if TYPE_CHECKING:
    from elements_rpg.save_load import GameSaveData


async def _load_state_or_raise(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> GameSaveData:
    """Load game state, raising ValueError if no save exists."""
    state = await load_game_state(db, player_id)
    if state is None:
        raise ValueError(f"No save found for player {player_id}")
    return state


async def get_balance(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, int]:
    """Get player's gold and gems balance.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.

    Returns:
        Dict with gold and gems values.
    """
    state = await _load_state_or_raise(db, player_id)
    return {"gold": state.economy.gold, "gems": state.economy.gems}


async def earn_gold(
    db: AsyncSession,
    player_id: uuid.UUID,
    amount: int,
    reason: str,
) -> dict[str, int]:
    """Add gold to the player's balance and persist.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        amount: Positive gold amount to add.
        reason: Description of why gold was earned.

    Returns:
        Dict with updated gold and gems balance.

    Raises:
        ValueError: If amount is not positive or no save exists.
    """
    state = await _load_state_or_raise(db, player_id)
    state.economy.earn_gold(amount, reason)
    await save_game_state(db, player_id, state)
    return {"gold": state.economy.gold, "gems": state.economy.gems}


async def spend_gold(
    db: AsyncSession,
    player_id: uuid.UUID,
    amount: int,
    reason: str,
) -> dict[str, int]:
    """Spend gold from the player's balance and persist.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        amount: Positive gold amount to spend.
        reason: Description of why gold was spent.

    Returns:
        Dict with updated gold and gems balance.

    Raises:
        ValueError: If amount is not positive, insufficient gold, or no save.
    """
    state = await _load_state_or_raise(db, player_id)
    success = state.economy.spend_gold(amount, reason)
    if not success:
        raise ValueError(f"Insufficient gold: have {state.economy.gold}, need {amount}")
    await save_game_state(db, player_id, state)
    return {"gold": state.economy.gold, "gems": state.economy.gems}


async def get_transactions(
    db: AsyncSession,
    player_id: uuid.UUID,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Get recent currency transactions.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        limit: Maximum number of transactions to return.

    Returns:
        List of transaction dicts, most recent first.
    """
    state = await _load_state_or_raise(db, player_id)
    transactions = state.economy.transaction_log[-limit:]
    transactions.reverse()
    return [t.model_dump() for t in transactions]


async def get_areas() -> list[dict[str, Any]]:
    """Get all available game areas.

    Returns:
        List of area data dicts.
    """
    return [area.model_dump() for area in MVP_AREAS.values()]


async def get_area(area_id: str) -> dict[str, Any] | None:
    """Get details of a specific area.

    Args:
        area_id: The area identifier.

    Returns:
        Area data dict if found, None otherwise.
    """
    area = MVP_AREAS.get(area_id)
    if area is None:
        return None
    return area.model_dump()
