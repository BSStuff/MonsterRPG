"""FastAPI dependency injection for ElementsRPG.

Database session dependency is implemented via db.session.get_db.
Auth and game state dependencies are stubs for Phase 2 (Supabase Auth).
"""

from __future__ import annotations

from typing import Any

from elements_rpg.db.session import get_db

# Re-export get_db as get_db_session for backward compatibility with routers
get_db_session = get_db


async def get_current_user() -> Any:
    """Get authenticated user from JWT. Stub for Phase 2 (Supabase Auth)."""
    raise NotImplementedError("Auth not configured yet. See Phase 2.")


async def get_game_state() -> Any:
    """Get player's current game state. Stub for Phase 2."""
    raise NotImplementedError("Game state loading not configured yet. See Phase 2.")
