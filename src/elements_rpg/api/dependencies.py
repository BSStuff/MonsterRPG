"""FastAPI dependency injection for ElementsRPG.

Database session dependency is implemented via db.session.get_db.
Auth dependency verifies Supabase JWTs via api.auth.get_current_user.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import uuid

from fastapi import HTTPException, status

from elements_rpg.api.auth import get_current_user  # noqa: F401 — re-exported
from elements_rpg.db.session import get_db
from elements_rpg.services.player_service import get_player_by_supabase_id

# Re-export get_db as get_db_session for backward compatibility with routers
get_db_session = get_db


async def resolve_player_id(
    db: Any,
    current_user: dict[str, Any],
) -> uuid.UUID:
    """Resolve the internal player UUID from the JWT sub claim.

    Shared dependency used by all routers that need the player's internal ID.
    Raises HTTPException 404 if no matching player is found.

    Args:
        db: The async database session.
        current_user: The decoded JWT payload containing at minimum 'sub'.

    Returns:
        The player's internal UUID.

    Raises:
        HTTPException: 404 if no player profile found for this account.
    """
    supabase_uid: str = current_user["sub"]
    player = await get_player_by_supabase_id(db, supabase_uid)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No player profile found for this account. Register first.",
        )
    return player.id
