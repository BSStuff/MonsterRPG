"""FastAPI dependency injection for ElementsRPG.

Database session dependency is implemented via db.session.get_db.
Auth dependency verifies Supabase JWTs via api.auth.get_current_user.
"""

from __future__ import annotations

from typing import Any

from elements_rpg.api.auth import get_current_user  # noqa: F401 — re-exported
from elements_rpg.db.session import get_db

# Re-export get_db as get_db_session for backward compatibility with routers
get_db_session = get_db


async def get_game_state() -> Any:
    """Get player's current game state. Stub for Phase 3."""
    raise NotImplementedError("Game state loading not configured yet. See Phase 3.")
