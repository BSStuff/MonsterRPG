"""Tests for premium currency system — gem packages, upgrades, store."""

import pytest
from pydantic import ValidationError

from monster_rpg.economy.manager import EconomyManager
from monster_rpg.economy.premium import (
    GEM_PACKAGES,
    PREMIUM_UPGRADES,
    GemPackage,
    PremiumStore,
    PremiumUpgrade,
    PurchaseResult,
    UpgradeType,
)


def _make_package(**overrides: object) -> GemPackage:
    """Create a GemPackage with sensible defaults."""
    defaults: dict[str, object] = {
        "package_id": "test_pkg",
        "name": "Test Package",
        "gem_amount": 100,
        "price_usd": 0.99,
    }
    defaults.update(overrides)
    return GemPackage(**defaults)


def _make_upgrade(**overrides: object) -> PremiumUpgrade:
    """Create a PremiumUpgrade with sensible defaults."""
    defaults: dict[str, object] = {
        "upgrade_id": "test_upgrade",
        "upgrade_type": UpgradeType.ACTION_QUEUE_SLOT,
        "name": "Test Upgrade",
        "description": "A test upgrade.",
        "gem_cost": 100,
        "max_purchases": 3,
        "effect_value": 1,
    }
    defaults.update(overrides)
    return PremiumUpgrade(**defaults)


def _make_economy(gems: int = 0) -> EconomyManager:
    """Create an EconomyManager with the given gem balance."""
    return EconomyManager(gems=gems)


class TestGemPackage:
    """Tests for GemPackage model."""

    def test_valid_construction(self) -> None:
        """GemPackage should accept valid data."""
        pkg = _make_package()
        assert pkg.package_id == "test_pkg"
        assert pkg.gem_amount == 100
        assert pkg.price_usd == 0.99
        assert pkg.bonus_gems == 0

    def test_with_bonus_gems(self) -> None:
        """GemPackage should accept bonus_gems."""
        pkg = _make_package(bonus_gems=50)
        assert pkg.bonus_gems == 50

    def test_total_gems_without_bonus(self) -> None:
        """total_gems should equal gem_amount when no bonus."""
        pkg = _make_package(gem_amount=200)
        assert pkg.total_gems == 200

    def test_total_gems_with_bonus(self) -> None:
        """total_gems should be gem_amount + bonus_gems."""
        pkg = _make_package(gem_amount=500, bonus_gems=50)
        assert pkg.total_gems == 550

    def test_price_per_gem_no_bonus(self) -> None:
        """price_per_gem should be price / gem_amount when no bonus."""
        pkg = _make_package(gem_amount=100, price_usd=1.00)
        assert pkg.price_per_gem == pytest.approx(0.01)

    def test_price_per_gem_with_bonus(self) -> None:
        """price_per_gem should account for bonus gems."""
        pkg = _make_package(gem_amount=100, bonus_gems=100, price_usd=1.00)
        assert pkg.price_per_gem == pytest.approx(0.005)

    def test_rejects_empty_package_id(self) -> None:
        """GemPackage should reject empty package_id."""
        with pytest.raises(ValidationError):
            _make_package(package_id="")

    def test_rejects_zero_gems(self) -> None:
        """GemPackage should reject gem_amount < 1."""
        with pytest.raises(ValidationError):
            _make_package(gem_amount=0)

    def test_rejects_zero_price(self) -> None:
        """GemPackage should reject price_usd <= 0."""
        with pytest.raises(ValidationError):
            _make_package(price_usd=0)

    def test_rejects_negative_bonus(self) -> None:
        """GemPackage should reject negative bonus_gems."""
        with pytest.raises(ValidationError):
            _make_package(bonus_gems=-1)

    def test_rejects_long_name(self) -> None:
        """GemPackage should reject name longer than 50 chars."""
        with pytest.raises(ValidationError):
            _make_package(name="A" * 51)


class TestUpgradeType:
    """Tests for UpgradeType enum."""

    def test_all_types_exist(self) -> None:
        """All four upgrade types should be defined."""
        assert set(UpgradeType) == {
            UpgradeType.ACTION_QUEUE_SLOT,
            UpgradeType.OFFLINE_CAP_INCREASE,
            UpgradeType.INVENTORY_EXPANSION,
            UpgradeType.TEAM_SLOT,
        }

    def test_values(self) -> None:
        """Upgrade type values should be snake_case strings."""
        assert UpgradeType.ACTION_QUEUE_SLOT.value == "action_queue_slot"
        assert UpgradeType.TEAM_SLOT.value == "team_slot"


class TestPremiumUpgrade:
    """Tests for PremiumUpgrade model."""

    def test_valid_construction(self) -> None:
        """PremiumUpgrade should accept valid data."""
        upgrade = _make_upgrade()
        assert upgrade.upgrade_id == "test_upgrade"
        assert upgrade.upgrade_type == UpgradeType.ACTION_QUEUE_SLOT
        assert upgrade.gem_cost == 100
        assert upgrade.max_purchases == 3

    def test_rejects_zero_gem_cost(self) -> None:
        """PremiumUpgrade should reject gem_cost < 1."""
        with pytest.raises(ValidationError):
            _make_upgrade(gem_cost=0)

    def test_rejects_zero_max_purchases(self) -> None:
        """PremiumUpgrade should reject max_purchases < 1."""
        with pytest.raises(ValidationError):
            _make_upgrade(max_purchases=0)

    def test_rejects_empty_upgrade_id(self) -> None:
        """PremiumUpgrade should reject empty upgrade_id."""
        with pytest.raises(ValidationError):
            _make_upgrade(upgrade_id="")


class TestPurchaseResult:
    """Tests for PurchaseResult model."""

    def test_success_result(self) -> None:
        """PurchaseResult should represent a successful purchase."""
        result = PurchaseResult(success=True, gems_spent=100, gems_remaining=400)
        assert result.success is True
        assert result.gems_spent == 100
        assert result.gems_remaining == 400
        assert result.error is None

    def test_failure_result(self) -> None:
        """PurchaseResult should represent a failed purchase."""
        result = PurchaseResult(success=False, gems_remaining=50, error="Insufficient gems")
        assert result.success is False
        assert result.gems_spent == 0
        assert result.error == "Insufficient gems"


class TestPremiumStore:
    """Tests for PremiumStore."""

    def test_initial_purchase_count_is_zero(self) -> None:
        """New store should report 0 purchases for any upgrade."""
        store = PremiumStore()
        assert store.get_purchase_count("anything") == 0

    def test_can_purchase_success(self) -> None:
        """can_purchase_upgrade should allow when gems and count are sufficient."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=100, max_purchases=3)
        can_buy, error = store.can_purchase_upgrade(upgrade, current_gems=500)
        assert can_buy is True
        assert error is None

    def test_can_purchase_insufficient_gems(self) -> None:
        """can_purchase_upgrade should reject when gems are insufficient."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=100)
        can_buy, error = store.can_purchase_upgrade(upgrade, current_gems=50)
        assert can_buy is False
        assert error == "Insufficient gems"

    def test_can_purchase_max_reached(self) -> None:
        """can_purchase_upgrade should reject when max purchases reached."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=100, max_purchases=1)
        # Buy once
        economy = _make_economy(gems=500)
        store.purchase_upgrade(upgrade, economy)
        # Try again
        can_buy, error = store.can_purchase_upgrade(upgrade, current_gems=500)
        assert can_buy is False
        assert error == "Maximum purchases reached"

    def test_purchase_upgrade_success(self) -> None:
        """purchase_upgrade should deduct gems and track count."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=200)
        economy = _make_economy(gems=500)
        result = store.purchase_upgrade(upgrade, economy)
        assert result.success is True
        assert result.gems_spent == 200
        assert result.gems_remaining == 300
        assert result.error is None
        assert store.get_purchase_count("test_upgrade") == 1
        assert economy.gems == 300

    def test_purchase_upgrade_fail_insufficient_gems(self) -> None:
        """purchase_upgrade should fail gracefully with insufficient gems."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=200)
        economy = _make_economy(gems=100)
        result = store.purchase_upgrade(upgrade, economy)
        assert result.success is False
        assert result.gems_spent == 0
        assert result.gems_remaining == 100
        assert result.error == "Insufficient gems"
        assert store.get_purchase_count("test_upgrade") == 0
        assert economy.gems == 100

    def test_purchase_upgrade_fail_max_reached(self) -> None:
        """purchase_upgrade should fail when max purchases already reached."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=100, max_purchases=1)
        economy = _make_economy(gems=1000)
        store.purchase_upgrade(upgrade, economy)
        result = store.purchase_upgrade(upgrade, economy)
        assert result.success is False
        assert result.error == "Maximum purchases reached"

    def test_multiple_purchases_up_to_max(self) -> None:
        """Should allow purchases up to max_purchases and then reject."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=50, max_purchases=3)
        economy = _make_economy(gems=10000)
        for i in range(3):
            result = store.purchase_upgrade(upgrade, economy)
            assert result.success is True, f"Purchase {i + 1} should succeed"
        assert store.get_purchase_count("test_upgrade") == 3
        result = store.purchase_upgrade(upgrade, economy)
        assert result.success is False
        assert result.error == "Maximum purchases reached"

    def test_purchase_exact_gem_amount(self) -> None:
        """Should succeed when gems exactly equal the cost."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=100)
        economy = _make_economy(gems=100)
        result = store.purchase_upgrade(upgrade, economy)
        assert result.success is True
        assert result.gems_remaining == 0
        assert economy.gems == 0

    def test_independent_upgrade_tracking(self) -> None:
        """Purchase counts should be tracked independently per upgrade_id."""
        store = PremiumStore()
        upgrade_a = _make_upgrade(upgrade_id="upgrade_a", max_purchases=2)
        upgrade_b = _make_upgrade(upgrade_id="upgrade_b", max_purchases=2)
        economy = _make_economy(gems=10000)
        store.purchase_upgrade(upgrade_a, economy)
        store.purchase_upgrade(upgrade_a, economy)
        assert store.get_purchase_count("upgrade_a") == 2
        assert store.get_purchase_count("upgrade_b") == 0
        result = store.purchase_upgrade(upgrade_b, economy)
        assert result.success is True

    def test_purchase_records_transaction(self) -> None:
        """purchase_upgrade should create a transaction in EconomyManager."""
        store = PremiumStore()
        upgrade = _make_upgrade(gem_cost=200)
        economy = _make_economy(gems=500)
        store.purchase_upgrade(upgrade, economy)
        assert len(economy.transaction_log) == 1
        assert economy.transaction_log[0].currency_type == "gems"
        assert economy.transaction_log[0].amount == -200


class TestGemPackageCatalog:
    """Tests for the GEM_PACKAGES catalog."""

    def test_catalog_has_five_entries(self) -> None:
        """GEM_PACKAGES should contain exactly 5 packages."""
        assert len(GEM_PACKAGES) == 5

    def test_prices_increase(self) -> None:
        """Package prices should increase from first to last."""
        prices = [pkg.price_usd for pkg in GEM_PACKAGES]
        assert prices == sorted(prices)
        assert len(set(prices)) == len(prices), "Prices should be unique"

    def test_gem_amounts_increase(self) -> None:
        """Base gem amounts should increase from first to last."""
        amounts = [pkg.gem_amount for pkg in GEM_PACKAGES]
        assert amounts == sorted(amounts)

    def test_total_gems_increase(self) -> None:
        """Total gems (base + bonus) should increase from first to last."""
        totals = [pkg.total_gems for pkg in GEM_PACKAGES]
        assert totals == sorted(totals)

    def test_price_per_gem_decreases(self) -> None:
        """Bigger packages should offer better value (lower price per gem)."""
        prices_per_gem = [pkg.price_per_gem for pkg in GEM_PACKAGES]
        assert prices_per_gem == sorted(prices_per_gem, reverse=True)


class TestPremiumUpgradeCatalog:
    """Tests for the PREMIUM_UPGRADES catalog."""

    def test_catalog_has_four_entries(self) -> None:
        """PREMIUM_UPGRADES should contain exactly 4 upgrades."""
        assert len(PREMIUM_UPGRADES) == 4

    def test_all_upgrade_types_covered(self) -> None:
        """Every UpgradeType should have at least one upgrade in the catalog."""
        types_in_catalog = {u.upgrade_type for u in PREMIUM_UPGRADES}
        assert types_in_catalog == set(UpgradeType)

    def test_all_ids_unique(self) -> None:
        """All upgrade IDs should be unique."""
        ids = [u.upgrade_id for u in PREMIUM_UPGRADES]
        assert len(ids) == len(set(ids))

    def test_all_costs_positive(self) -> None:
        """All gem costs should be positive."""
        for upgrade in PREMIUM_UPGRADES:
            assert upgrade.gem_cost > 0, f"{upgrade.upgrade_id} has non-positive cost"
