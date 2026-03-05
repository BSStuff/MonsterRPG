"""Tests for the subscription tier system."""

import pytest

from elements_rpg.economy.subscription import (
    SUBSCRIPTION_PLANS,
    PlayerSubscription,
    SubscriptionBenefits,
    SubscriptionPlan,
    SubscriptionTier,
)

# ==========================================
# SubscriptionTier enum tests
# ==========================================


class TestSubscriptionTier:
    """Tests for SubscriptionTier enum."""

    def test_has_none(self) -> None:
        assert SubscriptionTier.NONE == "none"

    def test_has_monthly(self) -> None:
        assert SubscriptionTier.MONTHLY == "monthly"

    def test_has_quarterly(self) -> None:
        assert SubscriptionTier.QUARTERLY == "quarterly"

    def test_has_annual(self) -> None:
        assert SubscriptionTier.ANNUAL == "annual"

    def test_enum_count(self) -> None:
        assert len(SubscriptionTier) == 4


# ==========================================
# SubscriptionBenefits tests
# ==========================================


class TestSubscriptionBenefits:
    """Tests for SubscriptionBenefits model."""

    def test_defaults(self) -> None:
        benefits = SubscriptionBenefits()
        assert benefits.ad_removal is True
        assert benefits.idle_cap_bonus_hours == 0.8
        assert benefits.queue_slot_bonus == 1
        assert benefits.daily_gem_stipend == 50
        assert benefits.exclusive_cosmetics is True

    def test_custom_values(self) -> None:
        benefits = SubscriptionBenefits(
            idle_cap_bonus_hours=1.6,
            queue_slot_bonus=2,
            daily_gem_stipend=75,
        )
        assert benefits.idle_cap_bonus_hours == 1.6
        assert benefits.queue_slot_bonus == 2
        assert benefits.daily_gem_stipend == 75

    def test_idle_cap_bonus_must_be_non_negative(self) -> None:
        with pytest.raises(ValueError):
            SubscriptionBenefits(idle_cap_bonus_hours=-1)


# ==========================================
# SubscriptionPlan tests
# ==========================================


class TestSubscriptionPlan:
    """Tests for SubscriptionPlan model."""

    def test_construction(self) -> None:
        plan = SubscriptionPlan(
            plan_id="test_plan",
            tier=SubscriptionTier.MONTHLY,
            name="Test Plan",
            duration_days=30,
            price_usd=4.99,
            benefits=SubscriptionBenefits(),
        )
        assert plan.plan_id == "test_plan"
        assert plan.tier == SubscriptionTier.MONTHLY
        assert plan.duration_days == 30
        assert plan.price_usd == 4.99

    def test_price_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            SubscriptionPlan(
                plan_id="bad",
                tier=SubscriptionTier.MONTHLY,
                name="Bad",
                duration_days=30,
                price_usd=0,
                benefits=SubscriptionBenefits(),
            )

    def test_plan_id_must_be_non_empty(self) -> None:
        with pytest.raises(ValueError):
            SubscriptionPlan(
                plan_id="",
                tier=SubscriptionTier.MONTHLY,
                name="Bad",
                duration_days=30,
                price_usd=4.99,
                benefits=SubscriptionBenefits(),
            )


# ==========================================
# PlayerSubscription tests
# ==========================================


class TestPlayerSubscription:
    """Tests for PlayerSubscription model."""

    @pytest.fixture()
    def monthly_plan(self) -> SubscriptionPlan:
        return SUBSCRIPTION_PLANS[SubscriptionTier.MONTHLY]

    @pytest.fixture()
    def active_sub(self, monthly_plan: SubscriptionPlan) -> PlayerSubscription:
        return PlayerSubscription(
            active_plan=monthly_plan,
            start_timestamp=1000.0,
            end_timestamp=2000.0,
            auto_renew=True,
        )

    @pytest.fixture()
    def inactive_sub(self) -> PlayerSubscription:
        return PlayerSubscription()

    def test_is_active_when_active(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.is_active(current_time=1500.0) is True

    def test_is_active_when_inactive(self, inactive_sub: PlayerSubscription) -> None:
        assert inactive_sub.is_active(current_time=1500.0) is False

    def test_is_active_with_plan_but_zero_end(self, monthly_plan: SubscriptionPlan) -> None:
        sub = PlayerSubscription(active_plan=monthly_plan, end_timestamp=0)
        assert sub.is_active(current_time=0.0) is False

    def test_is_active_expired(self, active_sub: PlayerSubscription) -> None:
        """Subscription should be inactive when current_time >= end_timestamp."""
        assert active_sub.is_active(current_time=2000.0) is False
        assert active_sub.is_active(current_time=3000.0) is False

    def test_get_benefits_when_active(self, active_sub: PlayerSubscription) -> None:
        benefits = active_sub.get_benefits(current_time=1500.0)
        assert benefits is not None
        assert benefits.ad_removal is True

    def test_get_benefits_when_inactive(self, inactive_sub: PlayerSubscription) -> None:
        assert inactive_sub.get_benefits(current_time=1500.0) is None

    def test_get_benefits_when_expired(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.get_benefits(current_time=5000.0) is None

    def test_get_idle_cap_bonus_active(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.get_idle_cap_bonus(current_time=1500.0) == 0.8

    def test_get_idle_cap_bonus_inactive(self, inactive_sub: PlayerSubscription) -> None:
        assert inactive_sub.get_idle_cap_bonus(current_time=1500.0) == 0.0

    def test_get_idle_cap_bonus_expired(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.get_idle_cap_bonus(current_time=5000.0) == 0.0

    def test_get_queue_slot_bonus_active(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.get_queue_slot_bonus(current_time=1500.0) == 1

    def test_get_queue_slot_bonus_inactive(self, inactive_sub: PlayerSubscription) -> None:
        assert inactive_sub.get_queue_slot_bonus(current_time=1500.0) == 0

    def test_get_daily_gem_stipend_active(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.get_daily_gem_stipend(current_time=1500.0) == 50

    def test_get_daily_gem_stipend_inactive(self, inactive_sub: PlayerSubscription) -> None:
        assert inactive_sub.get_daily_gem_stipend(current_time=1500.0) == 0

    def test_has_ad_removal_active(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.has_ad_removal(current_time=1500.0) is True

    def test_has_ad_removal_inactive(self, inactive_sub: PlayerSubscription) -> None:
        assert inactive_sub.has_ad_removal(current_time=1500.0) is False

    def test_has_ad_removal_expired(self, active_sub: PlayerSubscription) -> None:
        assert active_sub.has_ad_removal(current_time=5000.0) is False


# ==========================================
# SUBSCRIPTION_PLANS catalog tests
# ==========================================


class TestSubscriptionPlans:
    """Tests for the global subscription plan catalog."""

    def test_has_three_plans(self) -> None:
        assert len(SUBSCRIPTION_PLANS) == 3
        assert SubscriptionTier.MONTHLY in SUBSCRIPTION_PLANS
        assert SubscriptionTier.QUARTERLY in SUBSCRIPTION_PLANS
        assert SubscriptionTier.ANNUAL in SUBSCRIPTION_PLANS

    def test_annual_has_best_idle_bonus(self) -> None:
        annual = SUBSCRIPTION_PLANS[SubscriptionTier.ANNUAL]
        monthly = SUBSCRIPTION_PLANS[SubscriptionTier.MONTHLY]
        assert annual.benefits.idle_cap_bonus_hours > monthly.benefits.idle_cap_bonus_hours

    def test_quarterly_has_better_stipend_than_monthly(self) -> None:
        quarterly = SUBSCRIPTION_PLANS[SubscriptionTier.QUARTERLY]
        monthly = SUBSCRIPTION_PLANS[SubscriptionTier.MONTHLY]
        assert quarterly.benefits.daily_gem_stipend > monthly.benefits.daily_gem_stipend

    def test_annual_has_best_queue_bonus(self) -> None:
        annual = SUBSCRIPTION_PLANS[SubscriptionTier.ANNUAL]
        monthly = SUBSCRIPTION_PLANS[SubscriptionTier.MONTHLY]
        assert annual.benefits.queue_slot_bonus > monthly.benefits.queue_slot_bonus
