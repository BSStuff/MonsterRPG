"""FastAPI dependency injection stubs for ElementsRPG.

These will be implemented in Phase 2 (Supabase integration).
For now they provide the interface that routers will depend on.
"""

from __future__ import annotations

from typing import Any


async def get_db_session() -> Any:
    """Get database session. Stub for Phase 2 (Supabase)."""
    raise NotImplementedError("Database not configured yet. See Phase 2.")


async def get_current_user() -> Any:
    """Get authenticated user from JWT. Stub for Phase 2 (Supabase Auth)."""
    raise NotImplementedError("Auth not configured yet. See Phase 2.")


async def get_game_state() -> Any:
    """Get player's current game state. Stub for Phase 2."""
    raise NotImplementedError("Game state loading not configured yet. See Phase 2.")
