"""Tests for offline gains calculation."""

import pytest
from pydantic import ValidationError

from monster_rpg.config import OFFLINE_CAP_HOURS
from monster_rpg.idle.offline_gains import OfflineGainsResult, calculate_offline_gains
from monster_rpg.idle.tracker import AreaClearRecord, IdleTracker


def _make_tracker_with_clear(
    area_id: str = "forest_1",
    clear_time: float = 60.0,
    monsters: int = 10,
) -> IdleTracker:
    """Helper to create a tracker with one recorded clear."""
    tracker = IdleTracker()
    record = AreaClearRecord(
        area_id=area_id,
        clear_time_seconds=clear_time,
        monsters_defeated=monsters,
        timestamp=1000.0,
    )
    tracker.record_clear(record)
    return tracker


class TestOfflineGainsResultValidation:
    """Tests for OfflineGainsResult fields."""

    def test_valid_result(self) -> None:
        """Valid result creates successfully."""
        result = OfflineGainsResult(
            area_id="forest_1",
            offline_duration_hours=4.0,
            capped_duration_hours=4.0,
            idle_rate=0.85,
            total_rounds=204,
            estimated_monsters_defeated=2040,
            estimated_xp=20400,
            estimated_gold=10200,
            was_capped=False,
        )
        assert result.area_id == "forest_1"
        assert result.was_capped is False

    def test_empty_area_id_rejected(self) -> None:
        """Empty area_id is rejected."""
        with pytest.raises(ValidationError):
            OfflineGainsResult(
                area_id="",
                offline_duration_hours=0,
                capped_duration_hours=0,
                idle_rate=0,
                total_rounds=0,
                estimated_monsters_defeated=0,
                estimated_xp=0,
                estimated_gold=0,
                was_capped=False,
            )


class TestCalculateOfflineGainsZeroDuration:
    """Tests for zero/negative duration edge cases."""

    def test_zero_duration_returns_zeros(self) -> None:
        """Zero offline duration returns all-zero result."""
        tracker = _make_tracker_with_clear()
        result = calculate_offline_gains(tracker, "forest_1", 0.0)
        assert result.total_rounds == 0
        assert result.estimated_monsters_defeated == 0
        assert result.estimated_xp == 0
        assert result.estimated_gold == 0
        assert result.was_capped is False

    def test_negative_duration_returns_zeros(self) -> None:
        """Negative offline duration treated as zero."""
        tracker = _make_tracker_with_clear()
        result = calculate_offline_gains(tracker, "forest_1", -5.0)
        assert result.total_rounds == 0
        assert result.offline_duration_hours == 0


class TestCalculateOfflineGainsBasic:
    """Tests for basic offline gains calculation."""

    def test_basic_calculation(self) -> None:
        """1 hour offline, 60s clear, 10 monsters -> known result."""
        tracker = _make_tracker_with_clear(
            clear_time=60.0,
            monsters=10,
        )
        result = calculate_offline_gains(tracker, "forest_1", 1.0)

        # idle_rate = (60/60) * 0.85 = 0.85 rounds/min
        # total_rounds = int(0.85 * 60) = 51
        assert result.idle_rate == pytest.approx(0.85)
        assert result.total_rounds == 51

        # monsters_per_min = 10 * 0.85 = 8.5
        # total_monsters = int(8.5 * 60) = 510
        assert result.estimated_monsters_defeated == 510
        assert result.estimated_xp == 510 * 10
        assert result.estimated_gold == 510 * 5
        assert result.was_capped is False

    def test_4_hours_offline(self) -> None:
        """4 hours offline within cap."""
        tracker = _make_tracker_with_clear(clear_time=30.0, monsters=5)
        result = calculate_offline_gains(tracker, "forest_1", 4.0)

        # BRPM = 60/30 = 2, idle_rate = 2*0.85 = 1.7
        # total_minutes = 240, total_rounds = int(1.7*240) = 408
        assert result.idle_rate == pytest.approx(1.7)
        assert result.total_rounds == 408
        assert result.capped_duration_hours == 4.0
        assert result.was_capped is False


class TestOfflineCap:
    """Tests for the offline cap."""

    def test_cap_applied_at_12_hours(self) -> None:
        """12 hours offline gets capped to 8."""
        tracker = _make_tracker_with_clear(clear_time=60.0, monsters=10)
        result = calculate_offline_gains(tracker, "forest_1", 12.0)

        assert result.offline_duration_hours == 12.0
        assert result.capped_duration_hours == OFFLINE_CAP_HOURS
        assert result.was_capped is True

    def test_exactly_at_cap_not_flagged(self) -> None:
        """Exactly 8 hours is not considered capped."""
        tracker = _make_tracker_with_clear()
        result = calculate_offline_gains(tracker, "forest_1", 8.0)
        assert result.was_capped is False
        assert result.capped_duration_hours == 8.0

    def test_just_over_cap_is_flagged(self) -> None:
        """8.01 hours is capped."""
        tracker = _make_tracker_with_clear()
        result = calculate_offline_gains(tracker, "forest_1", 8.01)
        assert result.was_capped is True
        assert result.capped_duration_hours == OFFLINE_CAP_HOURS

    def test_custom_cap(self) -> None:
        """Custom offline cap overrides default."""
        tracker = _make_tracker_with_clear()
        result = calculate_offline_gains(
            tracker,
            "forest_1",
            20.0,
            offline_cap_hours=16.0,
        )
        assert result.capped_duration_hours == 16.0
        assert result.was_capped is True


class TestNoRecordedClears:
    """Tests when no clears have been recorded."""

    def test_no_clears_returns_zero_gains(self) -> None:
        """No recorded clears means idle rate is 0, so no gains."""
        tracker = IdleTracker()
        result = calculate_offline_gains(tracker, "forest_1", 4.0)
        assert result.idle_rate == 0.0
        assert result.total_rounds == 0
        assert result.estimated_monsters_defeated == 0
        assert result.estimated_xp == 0
        assert result.estimated_gold == 0


class TestCustomRewardRates:
    """Tests for custom xp_per_monster and gold_per_monster."""

    def test_custom_xp_per_monster(self) -> None:
        """Custom XP rate scales correctly."""
        tracker = _make_tracker_with_clear(clear_time=60.0, monsters=10)
        result = calculate_offline_gains(
            tracker,
            "forest_1",
            1.0,
            xp_per_monster=25,
        )
        assert result.estimated_xp == result.estimated_monsters_defeated * 25

    def test_custom_gold_per_monster(self) -> None:
        """Custom gold rate scales correctly."""
        tracker = _make_tracker_with_clear(clear_time=60.0, monsters=10)
        result = calculate_offline_gains(
            tracker,
            "forest_1",
            1.0,
            gold_per_monster=20,
        )
        assert result.estimated_gold == result.estimated_monsters_defeated * 20

    def test_custom_both_rates(self) -> None:
        """Both custom rates apply independently."""
        tracker = _make_tracker_with_clear(clear_time=60.0, monsters=10)
        result = calculate_offline_gains(
            tracker,
            "forest_1",
            1.0,
            xp_per_monster=50,
            gold_per_monster=100,
        )
        assert result.estimated_xp == result.estimated_monsters_defeated * 50
        assert result.estimated_gold == result.estimated_monsters_defeated * 100
