"""Premium router — gem packages, upgrades, subscriptions, and reward ads endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.api.auth import get_current_user
from elements_rpg.api.schemas import SuccessResponse
from elements_rpg.db.session import get_db
from elements_rpg.services.player_service import get_player_by_supabase_id
from elements_rpg.services.premium_service import (
    activate_subscription as service_activate_subscription,
)
from elements_rpg.services.premium_service import (
    cancel_subscription as service_cancel_subscription,
)
from elements_rpg.services.premium_service import (
    get_active_subscription as service_get_active_subscription,
)
from elements_rpg.services.premium_service import (
    get_ad_tracker as service_get_ad_tracker,
)
from elements_rpg.services.premium_service import (
    get_available_ads as service_get_available_ads,
)
from elements_rpg.services.premium_service import (
    get_gem_packages as service_get_gem_packages,
)
from elements_rpg.services.premium_service import (
    get_purchases as service_get_purchases,
)
from elements_rpg.services.premium_service import (
    get_subscription_plans as service_get_subscription_plans,
)
from elements_rpg.services.premium_service import (
    get_upgrades as service_get_upgrades,
)
from elements_rpg.services.premium_service import (
    purchase_upgrade as service_purchase_upgrade,
)
from elements_rpg.services.premium_service import (
    record_ad_watch as service_record_ad_watch,
)

router = APIRouter(prefix="/premium", tags=["Premium & Monetization"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ActivateSubscriptionRequest(BaseModel):
    """Request body for activating a subscription."""

    plan_id: str = Field(min_length=1, description="Subscription plan ID to activate")


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
# Gem Packages & Upgrades (public + authenticated)
# ---------------------------------------------------------------------------


@router.get("/packages")
async def list_packages() -> SuccessResponse[list[dict[str, Any]]]:
    """List available gem packages with prices."""
    packages = service_get_gem_packages()
    return SuccessResponse(data=[p.model_dump() for p in packages])


@router.get("/upgrades")
async def list_upgrades() -> SuccessResponse[list[dict[str, Any]]]:
    """List available convenience upgrades purchasable with gems."""
    upgrades = service_get_upgrades()
    return SuccessResponse(data=[u.model_dump() for u in upgrades])


@router.post("/purchase/{upgrade_id}")
async def purchase_upgrade(
    upgrade_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Purchase a convenience upgrade with gems."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_purchase_upgrade(db, player_id, upgrade_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error or "Purchase failed",
        )

    return SuccessResponse(data=result.model_dump())


@router.get("/purchases")
async def get_purchases(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, int]]:
    """Get the player's premium upgrade purchase history."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        purchases = await service_get_purchases(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=purchases)


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------


@router.get("/subscriptions/plans")
async def list_subscription_plans() -> SuccessResponse[list[dict[str, Any]]]:
    """List available subscription tiers (monthly, quarterly, annual)."""
    plans = service_get_subscription_plans()
    return SuccessResponse(data=[p.model_dump() for p in plans])


@router.post("/subscriptions/activate")
async def activate_subscription(
    body: ActivateSubscriptionRequest,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Activate a subscription tier for the player."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_activate_subscription(db, player_id, body.plan_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.get("/subscriptions/active")
async def get_active_subscription(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any] | None]:
    """Get the player's current active subscription and benefits."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_get_active_subscription(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Cancel the player's active subscription."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_cancel_subscription(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


# ---------------------------------------------------------------------------
# Reward Ads
# ---------------------------------------------------------------------------


@router.get("/ads/available")
async def get_available_ads(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[list[dict[str, Any]]]:
    """List which ad reward types are available (respects cooldowns and daily limits)."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_get_available_ads(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.post("/ads/{reward_type}/watch")
async def watch_ad(
    reward_type: str,
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Record an ad watch and grant the corresponding reward."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_record_ad_watch(db, player_id, reward_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)


@router.get("/ads/tracker")
async def get_ad_tracker(
    current_user: dict[str, Any] = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> SuccessResponse[dict[str, Any]]:
    """Get ad watch history, cooldowns, and remaining daily watches."""
    player_id = await _resolve_player_id(db, current_user)
    try:
        result = await service_get_ad_tracker(db, player_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return SuccessResponse(data=result)
