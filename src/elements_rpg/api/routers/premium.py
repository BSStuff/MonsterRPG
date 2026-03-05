"""Premium router — gem packages, upgrades, subscriptions, and reward ads endpoints."""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/premium", tags=["Premium & Monetization"])


# --- Gem Packages & Upgrades ---


@router.get("/packages", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_packages() -> JSONResponse:
    """List available gem packages with prices."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List gem packages"},
    )


@router.get("/upgrades", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_upgrades() -> JSONResponse:
    """List available convenience upgrades purchasable with gems."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List convenience upgrades"},
    )


@router.post("/purchase/{upgrade_id}", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def purchase_upgrade(upgrade_id: str) -> JSONResponse:
    """Purchase a convenience upgrade with gems."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Purchase upgrade {upgrade_id}",
        },
    )


@router.get("/purchases", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_purchases() -> JSONResponse:
    """Get the player's purchase history."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get purchase history"},
    )


# --- Subscriptions ---


@router.get("/subscriptions/plans", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def list_subscription_plans() -> JSONResponse:
    """List available subscription tiers (monthly, quarterly, annual)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List subscription plans"},
    )


@router.post("/subscriptions/activate", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def activate_subscription() -> JSONResponse:
    """Activate a subscription tier for the player."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Activate subscription"},
    )


@router.get("/subscriptions/active", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_active_subscription() -> JSONResponse:
    """Get the player's current active subscription and benefits."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get active subscription"},
    )


@router.post("/subscriptions/cancel", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def cancel_subscription() -> JSONResponse:
    """Cancel the player's active subscription."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Cancel subscription"},
    )


# --- Reward Ads ---


@router.get("/ads/available", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_available_ads() -> JSONResponse:
    """List which ad reward types are available (respects cooldowns and daily limits)."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "List available ad rewards"},
    )


@router.post("/ads/{reward_type}/watch", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def watch_ad(reward_type: str) -> JSONResponse:
    """Record an ad watch and grant the corresponding reward."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={
            "status": "not_implemented",
            "endpoint": f"Watch ad for {reward_type} reward",
        },
    )


@router.get("/ads/tracker", status_code=HTTPStatus.NOT_IMPLEMENTED)
async def get_ad_tracker() -> JSONResponse:
    """Get ad watch history, cooldowns, and remaining daily watches."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_IMPLEMENTED,
        content={"status": "not_implemented", "endpoint": "Get ad watch tracker"},
    )
