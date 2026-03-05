"""Subscription tier system — monthly benefits."""

from enum import StrEnum

from pydantic import BaseModel, Field


class SubscriptionTier(StrEnum):
    """Available subscription tiers."""

    NONE = "none"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"


class SubscriptionBenefits(BaseModel):
    """Benefits provided by a subscription."""

    ad_removal: bool = Field(default=True)
    idle_cap_bonus_hours: float = Field(default=0.8, ge=0, description="Extra offline hours")
    queue_slot_bonus: int = Field(default=1, ge=0)
    daily_gem_stipend: int = Field(default=50, ge=0)
    exclusive_cosmetics: bool = Field(default=True)


class SubscriptionPlan(BaseModel):
    """A subscription plan definition."""

    plan_id: str = Field(min_length=1)
    tier: SubscriptionTier
    name: str = Field(min_length=1, max_length=50)
    duration_days: int = Field(ge=1)
    price_usd: float = Field(gt=0)
    benefits: SubscriptionBenefits


class PlayerSubscription(BaseModel):
    """A player's active subscription status."""

    active_plan: SubscriptionPlan | None = Field(default=None)
    start_timestamp: float = Field(default=0, ge=0)
    end_timestamp: float = Field(default=0, ge=0)
    auto_renew: bool = Field(default=False)

    @property
    def is_active(self) -> bool:
        """Check if the subscription is currently active."""
        return self.active_plan is not None and self.end_timestamp > 0

    def get_benefits(self) -> SubscriptionBenefits | None:
        """Get the benefits of the active subscription, or None if inactive."""
        if not self.is_active:
            return None
        return self.active_plan.benefits if self.active_plan else None

    def get_idle_cap_bonus(self) -> float:
        """Get extra offline cap hours from subscription."""
        benefits = self.get_benefits()
        return benefits.idle_cap_bonus_hours if benefits else 0.0

    def get_queue_slot_bonus(self) -> int:
        """Get extra action queue slots from subscription."""
        benefits = self.get_benefits()
        return benefits.queue_slot_bonus if benefits else 0

    def get_daily_gem_stipend(self) -> int:
        """Get daily gem stipend from subscription."""
        benefits = self.get_benefits()
        return benefits.daily_gem_stipend if benefits else 0

    def has_ad_removal(self) -> bool:
        """Check if subscription removes ads."""
        benefits = self.get_benefits()
        return benefits.ad_removal if benefits else False


# ==========================================
# SUBSCRIPTION PLAN CATALOG
# ==========================================
SUBSCRIPTION_PLANS: dict[SubscriptionTier, SubscriptionPlan] = {
    SubscriptionTier.MONTHLY: SubscriptionPlan(
        plan_id="sub_monthly",
        tier=SubscriptionTier.MONTHLY,
        name="Monthly Pass",
        duration_days=30,
        price_usd=4.99,
        benefits=SubscriptionBenefits(),
    ),
    SubscriptionTier.QUARTERLY: SubscriptionPlan(
        plan_id="sub_quarterly",
        tier=SubscriptionTier.QUARTERLY,
        name="Quarterly Pass",
        duration_days=90,
        price_usd=12.99,
        benefits=SubscriptionBenefits(daily_gem_stipend=60),
    ),
    SubscriptionTier.ANNUAL: SubscriptionPlan(
        plan_id="sub_annual",
        tier=SubscriptionTier.ANNUAL,
        name="Annual Pass",
        duration_days=365,
        price_usd=39.99,
        benefits=SubscriptionBenefits(
            idle_cap_bonus_hours=1.6,
            queue_slot_bonus=2,
            daily_gem_stipend=75,
        ),
    ),
}
