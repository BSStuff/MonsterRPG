"""Economy router — gold balance, transactions, and area information endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services.economy_service import (
    earn_gold as service_earn_gold,
)
from elements_rpg.services.economy_service import (
    get_area as service_get_area,
)
from elements_rpg.services.economy_service import (
    get_areas as service_get_areas,
)
from elements_rpg.services.economy_service import (
    get_balance as service_get_balance,
)
from elements_rpg.services.economy_service import (
    get_transactions as service_get_transactions,
)
from elements_rpg.services.economy_service import (
    spend_gold as service_spend_gold,
)
from elements_rpg.services.player_service import get_player_by_supabase_id

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/economy", tags=["Economy"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class GoldRequest(BaseModel):
    """Request body for earning or spending gold."""

    amount: int = Field(gt=0, description="Positive gold amount")
    reason: str = Field(min_length=1, max_length=200, description="Reason for transaction")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _resolve_player_id(
    db: AsyncSession,
    current_user: dict[str, Any],
) -> Any:
    """Resolve the internal player UUID from the JWT sub claim."""
    supabase_uid: str = current_user["sub"]
    player = await get_player_by_supabase_id(db, supabase_uid)
    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No player profile found for this account. Register first.",
        )
    return player.id


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.get("/balance")
async def get_balance(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, int]]:
    """Get the authenticated player's gold and gems balance."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        balance = await service_get_balance(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=balance)


@router.post("/gold/earn")
async def earn_gold(
    body: GoldRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, int]]:
    """Add gold to the player's balance (from combat, crafting, etc.)."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        balance = await service_earn_gold(db, player_id, body.amount, body.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=balance)


@router.post("/gold/spend")
async def spend_gold(
    body: GoldRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, int]]:
    """Spend gold with balance validation."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        balance = await service_spend_gold(db, player_id, body.amount, body.reason)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=balance)


@router.get("/transactions")
async def get_transactions(
    limit: int = Query(default=50, ge=1, le=200, description="Max transactions to return"),
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[list[dict[str, Any]]]:
    """Get recent transaction history for the player."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        transactions = await service_get_transactions(db, player_id, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=transactions)


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------


@router.get("/areas")
async def list_areas() -> SuccessResponse[list[dict[str, Any]]]:
    """List all available game areas."""
    areas = await service_get_areas()
    return SuccessResponse(data=areas)


@router.get("/areas/{area_id}")
async def get_area(area_id: str) -> SuccessResponse[dict[str, Any]]:
    """Get details of a specific area including monsters and materials."""
    area = await service_get_area(area_id)
    if area is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Area '{area_id}' not found",
        )
    return SuccessResponse(data=area)
