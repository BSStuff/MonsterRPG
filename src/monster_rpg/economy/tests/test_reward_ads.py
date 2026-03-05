"""Tests for the reward ad system."""

import pytest

from monster_rpg.economy.reward_ads import (
    AD_REWARD_CONFIGS,
    AdRewardConfig,
    AdRewardType,
    AdWatchRecord,
    RewardAdTracker,
)

# ==========================================
# AdRewardType enum tests
# ==========================================


class TestAdRewardType:
    """Tests for AdRewardType enum."""

    def test_has_revive(self) -> None:
        assert AdRewardType.REVIVE == "revive"

    def test_has_idle_boost(self) -> None:
        assert AdRewardType.IDLE_BOOST == "idle_boost"

    def test_has_taming_bonus(self) -> None:
        assert AdRewardType.TAMING_BONUS == "taming_bonus"

    def test_has_resource_boost(self) -> None:
        assert AdRewardType.RESOURCE_BOOST == "resource_boost"

    def test_enum_count(self) -> None:
        assert len(AdRewardType) == 4


# ==========================================
# AdRewardConfig tests
# ==========================================


class TestAdRewardConfig:
    """Tests for AdRewardConfig model."""

    def test_construction(self) -> None:
        config = AdRewardConfig(
            reward_type=AdRewardType.REVIVE,
            description="Test revive",
            bonus_value=0.5,
            daily_limit=3,
            cooldown_minutes=30,
        )
        assert config.reward_type == AdRewardType.REVIVE
        assert config.bonus_value == 0.5
        assert config.daily_limit == 3
        assert config.cooldown_minutes == 30
        assert config.duration_minutes == 0

    def test_bonus_value_must_be_positive(self) -> None:
        with pytest.raises(ValueError):
            AdRewardConfig(
                reward_type=AdRewardType.REVIVE,
                description="Bad",
                bonus_value=0,
                daily_limit=1,
                cooldown_minutes=0,
            )

    def test_daily_limit_must_be_at_least_one(self) -> None:
        with pytest.raises(ValueError):
            AdRewardConfig(
                reward_type=AdRewardType.REVIVE,
                description="Bad",
                bonus_value=1.0,
                daily_limit=0,
                cooldown_minutes=0,
            )

    def test_duration_defaults_to_zero(self) -> None:
        config = AdRewardConfig(
            reward_type=AdRewardType.TAMING_BONUS,
            description="Instant",
            bonus_value=0.15,
            daily_limit=5,
            cooldown_minutes=0,
        )
        assert config.duration_minutes == 0


# ==========================================
# AdWatchRecord tests
# ==========================================


class TestAdWatchRecord:
    """Tests for AdWatchRecord model."""

    def test_construction(self) -> None:
        record = AdWatchRecord(
            reward_type=AdRewardType.IDLE_BOOST,
            timestamp=1000.0,
            bonus_applied=0.25,
        )
        assert record.reward_type == AdRewardType.IDLE_BOOST
        assert record.timestamp == 1000.0
        assert record.bonus_applied == 0.25


# ==========================================
# RewardAdTracker tests
# ==========================================


class TestRewardAdTracker:
    """Tests for RewardAdTracker."""

    @pytest.fixture()
    def tracker(self) -> RewardAdTracker:
        return RewardAdTracker()

    @pytest.fixture()
    def revive_config(self) -> AdRewardConfig:
        return AD_REWARD_CONFIGS[AdRewardType.REVIVE]

    @pytest.fixture()
    def idle_config(self) -> AdRewardConfig:
        return AD_REWARD_CONFIGS[AdRewardType.IDLE_BOOST]

    def test_can_watch_success(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        can, reason = tracker.can_watch(revive_config, current_time=1000.0)
        assert can is True
        assert reason is None

    def test_can_watch_daily_limit_reached(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        # Revive daily limit is 3
        for i in range(3):
            tracker.record_watch(revive_config, current_time=float(i * 3600))
        can, reason = tracker.can_watch(revive_config, current_time=10000.0)
        assert can is False
        assert reason == "Daily limit reached"

    def test_can_watch_cooldown_not_elapsed(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        # Revive cooldown is 30 minutes = 1800 seconds
        tracker.record_watch(revive_config, current_time=1000.0)
        can, reason = tracker.can_watch(revive_config, current_time=1500.0)
        assert can is False
        assert reason == "Cooldown not elapsed"

    def test_can_watch_after_cooldown_elapsed(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        # 30 min cooldown = 1800s
        can, reason = tracker.can_watch(revive_config, current_time=2801.0)
        assert can is True
        assert reason is None

    def test_record_watch_increments_count(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        assert tracker.watches_today["revive"] == 1
        tracker.record_watch(revive_config, current_time=5000.0)
        assert tracker.watches_today["revive"] == 2

    def test_record_watch_updates_last_time(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        assert tracker.last_watch_time["revive"] == 1000.0
        tracker.record_watch(revive_config, current_time=5000.0)
        assert tracker.last_watch_time["revive"] == 5000.0

    def test_record_watch_returns_record(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        record = tracker.record_watch(revive_config, current_time=1000.0)
        assert isinstance(record, AdWatchRecord)
        assert record.reward_type == AdRewardType.REVIVE
        assert record.timestamp == 1000.0
        assert record.bonus_applied == 0.5

    def test_watch_history_populated(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        tracker.record_watch(revive_config, current_time=5000.0)
        assert len(tracker.watch_history) == 2
        assert tracker.watch_history[0].timestamp == 1000.0
        assert tracker.watch_history[1].timestamp == 5000.0

    def test_reset_daily_clears_counts(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        assert tracker.watches_today.get("revive", 0) == 1
        tracker.reset_daily()
        assert tracker.watches_today.get("revive", 0) == 0

    def test_reset_daily_does_not_clear_history(
        self, tracker: RewardAdTracker, revive_config: AdRewardConfig
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        tracker.reset_daily()
        assert len(tracker.watch_history) == 1

    def test_independent_tracking_per_reward_type(
        self,
        tracker: RewardAdTracker,
        revive_config: AdRewardConfig,
        idle_config: AdRewardConfig,
    ) -> None:
        tracker.record_watch(revive_config, current_time=1000.0)
        tracker.record_watch(idle_config, current_time=1000.0)
        assert tracker.watches_today["revive"] == 1
        assert tracker.watches_today["idle_boost"] == 1


# ==========================================
# AD_REWARD_CONFIGS tests
# ==========================================


class TestAdRewardConfigs:
    """Tests for the global ad reward configuration catalog."""

    def test_has_all_four_types(self) -> None:
        assert len(AD_REWARD_CONFIGS) == 4
        for reward_type in AdRewardType:
            assert reward_type in AD_REWARD_CONFIGS

    def test_revive_is_instant(self) -> None:
        config = AD_REWARD_CONFIGS[AdRewardType.REVIVE]
        assert config.duration_minutes == 0

    def test_idle_boost_has_duration(self) -> None:
        config = AD_REWARD_CONFIGS[AdRewardType.IDLE_BOOST]
        assert config.duration_minutes == 30
        assert config.bonus_value == 0.25

    def test_resource_boost_doubles_drops(self) -> None:
        config = AD_REWARD_CONFIGS[AdRewardType.RESOURCE_BOOST]
        assert config.bonus_value == 2.0
