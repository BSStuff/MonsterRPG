"""Reward ad system — optional ad viewing for in-game bonuses."""

from enum import StrEnum

from pydantic import BaseModel, Field


class AdRewardType(StrEnum):
    """Types of rewards from watching ads."""

    REVIVE = "revive"
    IDLE_BOOST = "idle_boost"
    TAMING_BONUS = "taming_bonus"
    RESOURCE_BOOST = "resource_boost"


class AdRewardConfig(BaseModel):
    """Configuration for a specific ad reward type."""

    reward_type: AdRewardType
    description: str
    bonus_value: float = Field(gt=0, description="Bonus multiplier or flat value")
    duration_minutes: int = Field(default=0, ge=0, description="Duration of effect (0 = instant)")
    daily_limit: int = Field(ge=1, description="Max watches per day")
    cooldown_minutes: int = Field(ge=0, description="Cooldown between watches")


class AdWatchRecord(BaseModel):
    """Record of an ad watch."""

    reward_type: AdRewardType
    timestamp: float = Field(ge=0)
    bonus_applied: float


class RewardAdTracker(BaseModel):
    """Tracks ad watches for cooldown and daily limit enforcement."""

    watches_today: dict[str, int] = Field(default_factory=dict)
    last_watch_time: dict[str, float] = Field(default_factory=dict)
    watch_history: list[AdWatchRecord] = Field(default_factory=list)

    def can_watch(
        self,
        config: AdRewardConfig,
        current_time: float,
    ) -> tuple[bool, str | None]:
        """Check if an ad can be watched.

        Args:
            config: The ad reward configuration to check against.
            current_time: Current timestamp in seconds.

        Returns:
            Tuple of (can_watch, reason_if_not).
        """
        key = config.reward_type.value
        # Daily limit
        count = self.watches_today.get(key, 0)
        if count >= config.daily_limit:
            return False, "Daily limit reached"
        # Cooldown (skip if never watched before)
        last = self.last_watch_time.get(key)
        if last is not None and (current_time - last) < config.cooldown_minutes * 60:
            return False, "Cooldown not elapsed"
        return True, None

    def record_watch(
        self,
        config: AdRewardConfig,
        current_time: float,
    ) -> AdWatchRecord:
        """Record an ad watch and return the watch record.

        Args:
            config: The ad reward configuration.
            current_time: Current timestamp in seconds.

        Returns:
            The recorded ad watch record.
        """
        key = config.reward_type.value
        self.watches_today[key] = self.watches_today.get(key, 0) + 1
        self.last_watch_time[key] = current_time
        record = AdWatchRecord(
            reward_type=config.reward_type,
            timestamp=current_time,
            bonus_applied=config.bonus_value,
        )
        self.watch_history.append(record)
        return record

    def reset_daily(self) -> None:
        """Reset daily watch counts (call at server midnight)."""
        self.watches_today.clear()


# ==========================================
# REWARD AD CONFIGURATIONS
# ==========================================
AD_REWARD_CONFIGS: dict[AdRewardType, AdRewardConfig] = {
    AdRewardType.REVIVE: AdRewardConfig(
        reward_type=AdRewardType.REVIVE,
        description="Revive all fainted monsters with 50% HP",
        bonus_value=0.5,
        duration_minutes=0,
        daily_limit=3,
        cooldown_minutes=30,
    ),
    AdRewardType.IDLE_BOOST: AdRewardConfig(
        reward_type=AdRewardType.IDLE_BOOST,
        description="Boost idle gains by 25% for 30 minutes",
        bonus_value=0.25,
        duration_minutes=30,
        daily_limit=5,
        cooldown_minutes=60,
    ),
    AdRewardType.TAMING_BONUS: AdRewardConfig(
        reward_type=AdRewardType.TAMING_BONUS,
        description="Increase next taming attempt chance by 15%",
        bonus_value=0.15,
        duration_minutes=0,
        daily_limit=5,
        cooldown_minutes=15,
    ),
    AdRewardType.RESOURCE_BOOST: AdRewardConfig(
        reward_type=AdRewardType.RESOURCE_BOOST,
        description="Double resource drops for 15 minutes",
        bonus_value=2.0,
        duration_minutes=15,
        daily_limit=3,
        cooldown_minutes=45,
    ),
}
