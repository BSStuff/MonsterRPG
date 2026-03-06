"""Premium service — gem packages, upgrades, subscriptions, and reward ads.

Bridges between API routers and the PremiumStore / PlayerSubscription /
RewardAdTracker models. All mutations follow load -> modify -> save pattern.
"""

from __future__ import annotations

import time
import uuid  # noqa: TC003 — used at runtime in function signatures
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.economy.premium import (
    GEM_PACKAGES,
    PREMIUM_UPGRADES,
    GemPackage,
    PremiumStore,
    PremiumUpgrade,
    PurchaseResult,
)
from elements_rpg.economy.reward_ads import (
    AD_REWARD_CONFIGS,
    AdRewardType,
)
from elements_rpg.economy.subscription import (
    SUBSCRIPTION_PLANS,
    PlayerSubscription,
    SubscriptionPlan,
)
from elements_rpg.services.save_service import load_game_state, save_game_state

# Re-export for convenience in router imports
__all__ = [
    "activate_subscription",
    "cancel_subscription",
    "get_active_subscription",
    "get_ad_tracker",
    "get_available_ads",
    "get_gem_packages",
    "get_purchases",
    "get_subscription_plans",
    "get_upgrades",
    "purchase_upgrade",
    "record_ad_watch",
]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_state_or_raise(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> Any:
    """Load game state, raising ValueError if no save exists."""
    state = await load_game_state(db, player_id)
    if state is None:
        raise ValueError(f"No save found for player {player_id}")
    return state


def _find_upgrade(upgrade_id: str) -> PremiumUpgrade | None:
    """Find a premium upgrade by ID from the catalog."""
    for upgrade in PREMIUM_UPGRADES:
        if upgrade.upgrade_id == upgrade_id:
            return upgrade
    return None


def _find_plan(plan_id: str) -> SubscriptionPlan | None:
    """Find a subscription plan by ID from the catalog."""
    for plan in SUBSCRIPTION_PLANS.values():
        if plan.plan_id == plan_id:
            return plan
    return None


# ---------------------------------------------------------------------------
# Gem Packages & Upgrades
# ---------------------------------------------------------------------------


def get_gem_packages() -> list[GemPackage]:
    """Get all available gem packages."""
    return GEM_PACKAGES


def get_upgrades() -> list[PremiumUpgrade]:
    """Get all available premium upgrades."""
    return PREMIUM_UPGRADES


async def purchase_upgrade(
    db: AsyncSession,
    player_id: uuid.UUID,
    upgrade_id: str,
) -> PurchaseResult:
    """Purchase a premium upgrade with gems.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        upgrade_id: The upgrade to purchase.

    Returns:
        PurchaseResult with success/failure details.

    Raises:
        ValueError: If no save exists or upgrade_id is invalid.
    """
    upgrade = _find_upgrade(upgrade_id)
    if upgrade is None:
        raise ValueError(f"Unknown upgrade: {upgrade_id}")

    state = await _load_state_or_raise(db, player_id)

    # Rebuild PremiumStore from saved purchase counts
    store = PremiumStore()
    store.purchase_counts = dict(state.premium_purchases)

    result = store.purchase_upgrade(upgrade, state.economy)
    if result.success:
        # Persist updated purchase counts and gem balance
        state.premium_purchases = dict(store.purchase_counts)
        await save_game_state(db, player_id, state)

    return result


async def get_purchases(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, int]:
    """Get the player's premium upgrade purchase history.

    Returns:
        Dict mapping upgrade_id to purchase count.
    """
    state = await _load_state_or_raise(db, player_id)
    return dict(state.premium_purchases)


# ---------------------------------------------------------------------------
# Subscriptions
# ---------------------------------------------------------------------------


def get_subscription_plans() -> list[SubscriptionPlan]:
    """Get all available subscription plans."""
    return list(SUBSCRIPTION_PLANS.values())


async def activate_subscription(
    db: AsyncSession,
    player_id: uuid.UUID,
    plan_id: str,
) -> dict[str, Any]:
    """Activate a subscription plan for the player.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        plan_id: The subscription plan to activate.

    Returns:
        Dict with subscription details.

    Raises:
        ValueError: If no save exists or plan_id is invalid.
    """
    plan = _find_plan(plan_id)
    if plan is None:
        raise ValueError(f"Unknown subscription plan: {plan_id}")

    state = await _load_state_or_raise(db, player_id)

    now = time.time()
    state.subscription = PlayerSubscription(
        active_plan=plan,
        start_timestamp=now,
        end_timestamp=now + (plan.duration_days * 86400),
        auto_renew=True,
    )
    await save_game_state(db, player_id, state)

    return {
        "plan_id": plan.plan_id,
        "tier": plan.tier.value,
        "name": plan.name,
        "start_timestamp": state.subscription.start_timestamp,
        "end_timestamp": state.subscription.end_timestamp,
        "benefits": plan.benefits.model_dump(),
    }


async def get_active_subscription(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Get the player's active subscription, or None if inactive.

    Returns:
        Dict with subscription details, or None.
    """
    state = await _load_state_or_raise(db, player_id)
    sub = state.subscription
    now = time.time()

    if not sub.is_active(now):
        return None

    return {
        "plan_id": sub.active_plan.plan_id,
        "tier": sub.active_plan.tier.value,
        "name": sub.active_plan.name,
        "start_timestamp": sub.start_timestamp,
        "end_timestamp": sub.end_timestamp,
        "auto_renew": sub.auto_renew,
        "benefits": sub.active_plan.benefits.model_dump(),
    }


async def cancel_subscription(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Cancel the player's active subscription.

    Returns:
        Dict with cancellation details.

    Raises:
        ValueError: If no save exists or no active subscription.
    """
    state = await _load_state_or_raise(db, player_id)
    sub = state.subscription
    now = time.time()

    if not sub.is_active(now):
        raise ValueError("No active subscription to cancel")

    plan_id = sub.active_plan.plan_id
    tier = sub.active_plan.tier.value

    # Disable auto-renew but keep benefits until end_timestamp
    state.subscription.auto_renew = False
    await save_game_state(db, player_id, state)

    return {
        "plan_id": plan_id,
        "tier": tier,
        "cancelled": True,
        "active_until": sub.end_timestamp,
    }


# ---------------------------------------------------------------------------
# Reward Ads
# ---------------------------------------------------------------------------


async def get_available_ads(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Get available ad rewards with cooldown/limit info.

    Returns:
        List of ad reward configs with availability status.
    """
    state = await _load_state_or_raise(db, player_id)
    tracker = state.ad_tracker
    now = time.time()

    results: list[dict[str, Any]] = []
    for reward_type, config in AD_REWARD_CONFIGS.items():
        can_watch, reason = tracker.can_watch(config, now)
        key = reward_type.value
        watches_today = tracker.watches_today.get(key, 0)
        last_watch = tracker.last_watch_time.get(key)

        cooldown_remaining = 0.0
        if last_watch is not None:
            elapsed = now - last_watch
            cooldown_secs = config.cooldown_minutes * 60
            if elapsed < cooldown_secs:
                cooldown_remaining = cooldown_secs - elapsed

        results.append(
            {
                "reward_type": reward_type.value,
                "description": config.description,
                "bonus_value": config.bonus_value,
                "duration_minutes": config.duration_minutes,
                "available": can_watch,
                "reason": reason,
                "watches_today": watches_today,
                "daily_limit": config.daily_limit,
                "cooldown_remaining_seconds": round(cooldown_remaining, 1),
            }
        )

    return results


async def record_ad_watch(
    db: AsyncSession,
    player_id: uuid.UUID,
    reward_type: str,
) -> dict[str, Any]:
    """Record an ad watch and apply the reward.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        reward_type: The type of ad reward (must match AdRewardType).

    Returns:
        Dict with watch result details.

    Raises:
        ValueError: If no save, invalid reward_type, or ad unavailable.
    """
    # Validate reward type
    try:
        ad_type = AdRewardType(reward_type)
    except ValueError:
        valid = [t.value for t in AdRewardType]
        raise ValueError(f"Invalid reward type: {reward_type}. Valid types: {valid}") from None

    config = AD_REWARD_CONFIGS.get(ad_type)
    if config is None:
        raise ValueError(f"No configuration for reward type: {reward_type}")

    state = await _load_state_or_raise(db, player_id)
    tracker = state.ad_tracker
    now = time.time()

    # Check availability before recording
    can_watch, reason = tracker.can_watch(config, now)
    if not can_watch:
        raise ValueError(f"Cannot watch ad: {reason}")

    record = tracker.record_watch(config, now)
    if record is None:
        raise ValueError("Failed to record ad watch")

    await save_game_state(db, player_id, state)

    return {
        "reward_type": record.reward_type.value,
        "bonus_applied": record.bonus_applied,
        "timestamp": record.timestamp,
        "watches_today": tracker.watches_today.get(ad_type.value, 0),
        "daily_limit": config.daily_limit,
    }


async def get_ad_tracker(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the player's ad watch tracker state.

    Returns:
        Dict with watch history, cooldowns, and daily counts.
    """
    state = await _load_state_or_raise(db, player_id)
    tracker = state.ad_tracker

    return {
        "watches_today": dict(tracker.watches_today),
        "last_watch_time": dict(tracker.last_watch_time),
        "watch_history": [r.model_dump() for r in tracker.watch_history],
    }
