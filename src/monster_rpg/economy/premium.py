"""Premium currency (Gems) system — packages, upgrades, price catalog."""

from enum import StrEnum

from pydantic import BaseModel, Field


class GemPackage(BaseModel):
    """A gem package available for purchase.

    Attributes:
        package_id: Unique identifier for the package.
        name: Display name of the package.
        gem_amount: Base gems included in the package.
        price_usd: Price in US dollars.
        bonus_gems: Extra gems as a bonus on top of gem_amount.
    """

    package_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=50)
    gem_amount: int = Field(ge=1)
    price_usd: float = Field(gt=0)
    bonus_gems: int = Field(default=0, ge=0, description="Extra gems as bonus")

    @property
    def total_gems(self) -> int:
        """Total gems received (base + bonus)."""
        return self.gem_amount + self.bonus_gems

    @property
    def price_per_gem(self) -> float:
        """Cost per gem in USD."""
        return self.price_usd / self.total_gems if self.total_gems > 0 else 0


class UpgradeType(StrEnum):
    """Types of gem-purchasable upgrades."""

    ACTION_QUEUE_SLOT = "action_queue_slot"
    OFFLINE_CAP_INCREASE = "offline_cap_increase"
    INVENTORY_EXPANSION = "inventory_expansion"
    TEAM_SLOT = "team_slot"


class PremiumUpgrade(BaseModel):
    """A premium upgrade purchasable with gems.

    Attributes:
        upgrade_id: Unique identifier for the upgrade.
        upgrade_type: Category of upgrade.
        name: Display name.
        description: Human-readable description of the upgrade effect.
        gem_cost: Cost in gems.
        max_purchases: Maximum times this upgrade can be bought.
        effect_value: Numeric value of the upgrade effect.
    """

    upgrade_id: str = Field(min_length=1)
    upgrade_type: UpgradeType
    name: str = Field(min_length=1, max_length=50)
    description: str
    gem_cost: int = Field(ge=1)
    max_purchases: int = Field(ge=1, description="Max times this can be bought")
    effect_value: float = Field(description="Numeric value of the upgrade effect")


class PurchaseResult(BaseModel):
    """Result of attempting a premium purchase.

    Attributes:
        success: Whether the purchase succeeded.
        gems_spent: Number of gems deducted.
        gems_remaining: Gem balance after the transaction.
        error: Error message if the purchase failed.
    """

    success: bool
    gems_spent: int = Field(default=0, ge=0)
    gems_remaining: int = Field(ge=0)
    error: str | None = Field(default=None)


class PremiumStore:
    """Manages premium currency purchases and upgrades.

    Tracks per-upgrade purchase counts and validates purchase eligibility.
    """

    def __init__(self) -> None:
        self.purchase_counts: dict[str, int] = {}

    def get_purchase_count(self, upgrade_id: str) -> int:
        """Get how many times an upgrade has been purchased."""
        return self.purchase_counts.get(upgrade_id, 0)

    def can_purchase_upgrade(
        self, upgrade: PremiumUpgrade, current_gems: int
    ) -> tuple[bool, str | None]:
        """Check if an upgrade can be purchased.

        Args:
            upgrade: The upgrade to check.
            current_gems: Player's current gem balance.

        Returns:
            Tuple of (can_buy, error_message). error_message is None if can_buy.
        """
        if current_gems < upgrade.gem_cost:
            return False, "Insufficient gems"
        count = self.get_purchase_count(upgrade.upgrade_id)
        if count >= upgrade.max_purchases:
            return False, "Maximum purchases reached"
        return True, None

    def purchase_upgrade(self, upgrade: PremiumUpgrade, current_gems: int) -> PurchaseResult:
        """Execute a premium upgrade purchase.

        Args:
            upgrade: The upgrade to purchase.
            current_gems: Player's current gem balance.

        Returns:
            PurchaseResult with success/failure details.
        """
        can_buy, error = self.can_purchase_upgrade(upgrade, current_gems)
        if not can_buy:
            return PurchaseResult(
                success=False,
                gems_remaining=current_gems,
                error=error,
            )
        new_gems = current_gems - upgrade.gem_cost
        self.purchase_counts[upgrade.upgrade_id] = self.get_purchase_count(upgrade.upgrade_id) + 1
        return PurchaseResult(
            success=True,
            gems_spent=upgrade.gem_cost,
            gems_remaining=new_gems,
        )


# ==========================================
# GEM PACKAGE CATALOG
# ==========================================
GEM_PACKAGES: list[GemPackage] = [
    GemPackage(
        package_id="gems_100",
        name="Handful of Gems",
        gem_amount=100,
        price_usd=0.99,
    ),
    GemPackage(
        package_id="gems_500",
        name="Pouch of Gems",
        gem_amount=500,
        price_usd=4.99,
        bonus_gems=50,
    ),
    GemPackage(
        package_id="gems_1200",
        name="Chest of Gems",
        gem_amount=1200,
        price_usd=9.99,
        bonus_gems=200,
    ),
    GemPackage(
        package_id="gems_3000",
        name="Treasure of Gems",
        gem_amount=3000,
        price_usd=19.99,
        bonus_gems=750,
    ),
    GemPackage(
        package_id="gems_7000",
        name="Hoard of Gems",
        gem_amount=7000,
        price_usd=49.99,
        bonus_gems=2500,
    ),
]

# ==========================================
# PREMIUM UPGRADE CATALOG
# ==========================================
PREMIUM_UPGRADES: list[PremiumUpgrade] = [
    PremiumUpgrade(
        upgrade_id="upgrade_queue_slot",
        upgrade_type=UpgradeType.ACTION_QUEUE_SLOT,
        name="Extra Queue Slot",
        description="Add one additional action queue slot.",
        gem_cost=200,
        max_purchases=6,
        effect_value=1,
    ),
    PremiumUpgrade(
        upgrade_id="upgrade_offline_cap",
        upgrade_type=UpgradeType.OFFLINE_CAP_INCREASE,
        name="Extended Offline",
        description="Increase offline cap by 2 hours.",
        gem_cost=300,
        max_purchases=4,
        effect_value=2,
    ),
    PremiumUpgrade(
        upgrade_id="upgrade_inventory",
        upgrade_type=UpgradeType.INVENTORY_EXPANSION,
        name="Inventory Expansion",
        description="Increase max stack size by 500.",
        gem_cost=150,
        max_purchases=5,
        effect_value=500,
    ),
    PremiumUpgrade(
        upgrade_id="upgrade_team_slot",
        upgrade_type=UpgradeType.TEAM_SLOT,
        name="Extra Team",
        description="Unlock an additional saved team.",
        gem_cost=500,
        max_purchases=3,
        effect_value=1,
    ),
]
