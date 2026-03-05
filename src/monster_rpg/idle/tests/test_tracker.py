"""Tests for the idle tracker."""

import pytest
from pydantic import ValidationError

from monster_rpg.config import IDLE_EFFICIENCY_RATE
from monster_rpg.idle.tracker import AreaClearRecord, IdleTracker

# --- AreaClearRecord validation ---


class TestAreaClearRecordValidation:
    """Tests for AreaClearRecord field validation."""

    def test_valid_record(self) -> None:
        """Valid record creates successfully."""
        record = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=30.0,
            monsters_defeated=5,
            timestamp=1000.0,
        )
        assert record.area_id == "forest_1"
        assert record.clear_time_seconds == 30.0
        assert record.monsters_defeated == 5

    def test_empty_area_id_rejected(self) -> None:
        """Empty area_id is rejected."""
        with pytest.raises(ValidationError):
            AreaClearRecord(
                area_id="",
                clear_time_seconds=30.0,
                monsters_defeated=5,
                timestamp=1000.0,
            )

    def test_zero_clear_time_rejected(self) -> None:
        """Zero clear time is rejected (must be gt=0)."""
        with pytest.raises(ValidationError):
            AreaClearRecord(
                area_id="forest_1",
                clear_time_seconds=0.0,
                monsters_defeated=5,
                timestamp=1000.0,
            )

    def test_negative_clear_time_rejected(self) -> None:
        """Negative clear time is rejected."""
        with pytest.raises(ValidationError):
            AreaClearRecord(
                area_id="forest_1",
                clear_time_seconds=-10.0,
                monsters_defeated=5,
                timestamp=1000.0,
            )

    def test_zero_monsters_rejected(self) -> None:
        """Zero monsters defeated is rejected (must be ge=1)."""
        with pytest.raises(ValidationError):
            AreaClearRecord(
                area_id="forest_1",
                clear_time_seconds=30.0,
                monsters_defeated=0,
                timestamp=1000.0,
            )

    def test_negative_timestamp_rejected(self) -> None:
        """Negative timestamp is rejected."""
        with pytest.raises(ValidationError):
            AreaClearRecord(
                area_id="forest_1",
                clear_time_seconds=30.0,
                monsters_defeated=5,
                timestamp=-1.0,
            )


# --- IdleTracker ---


class TestIdleTrackerInit:
    """Tests for IdleTracker initialization."""

    def test_starts_empty(self) -> None:
        """New tracker has no recorded data."""
        tracker = IdleTracker()
        assert tracker.best_clear_times == {}
        assert tracker.best_monsters_per_clear == {}


class TestRecordClear:
    """Tests for IdleTracker.record_clear()."""

    def test_first_clear_is_new_best(self) -> None:
        """First clear for an area is always a new best."""
        tracker = IdleTracker()
        record = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        result = tracker.record_clear(record)
        assert result is True
        assert tracker.best_clear_times["forest_1"] == 60.0
        assert tracker.best_monsters_per_clear["forest_1"] == 10

    def test_faster_time_updates_best(self) -> None:
        """A faster clear time replaces the previous best."""
        tracker = IdleTracker()
        slow = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        fast = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=30.0,
            monsters_defeated=8,
            timestamp=2000.0,
        )
        tracker.record_clear(slow)
        result = tracker.record_clear(fast)
        assert result is True
        assert tracker.best_clear_times["forest_1"] == 30.0
        assert tracker.best_monsters_per_clear["forest_1"] == 8

    def test_slower_time_ignored(self) -> None:
        """A slower clear time does not replace the best."""
        tracker = IdleTracker()
        fast = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=30.0,
            monsters_defeated=8,
            timestamp=1000.0,
        )
        slow = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=2000.0,
        )
        tracker.record_clear(fast)
        result = tracker.record_clear(slow)
        assert result is False
        assert tracker.best_clear_times["forest_1"] == 30.0
        assert tracker.best_monsters_per_clear["forest_1"] == 8

    def test_equal_time_ignored(self) -> None:
        """An equal clear time does not count as a new best."""
        tracker = IdleTracker()
        first = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=30.0,
            monsters_defeated=8,
            timestamp=1000.0,
        )
        second = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=30.0,
            monsters_defeated=12,
            timestamp=2000.0,
        )
        tracker.record_clear(first)
        result = tracker.record_clear(second)
        assert result is False
        # Original monsters count preserved
        assert tracker.best_monsters_per_clear["forest_1"] == 8


class TestGetBrpm:
    """Tests for IdleTracker.get_brpm()."""

    def test_brpm_60s_clear(self) -> None:
        """60-second clear = 1.0 BRPM."""
        tracker = IdleTracker()
        record = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        tracker.record_clear(record)
        assert tracker.get_brpm("forest_1") == pytest.approx(1.0)

    def test_brpm_30s_clear(self) -> None:
        """30-second clear = 2.0 BRPM."""
        tracker = IdleTracker()
        record = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=30.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        tracker.record_clear(record)
        assert tracker.get_brpm("forest_1") == pytest.approx(2.0)

    def test_brpm_unrecorded_area(self) -> None:
        """BRPM for an unrecorded area returns 0.0."""
        tracker = IdleTracker()
        assert tracker.get_brpm("unknown_area") == 0.0

    def test_brpm_120s_clear(self) -> None:
        """120-second clear = 0.5 BRPM."""
        tracker = IdleTracker()
        record = AreaClearRecord(
            area_id="cave_1",
            clear_time_seconds=120.0,
            monsters_defeated=20,
            timestamp=1000.0,
        )
        tracker.record_clear(record)
        assert tracker.get_brpm("cave_1") == pytest.approx(0.5)


class TestGetIdleRate:
    """Tests for IdleTracker.get_idle_rate()."""

    def test_idle_rate_is_85_percent_of_brpm(self) -> None:
        """Idle rate = BRPM * 0.85."""
        tracker = IdleTracker()
        record = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        tracker.record_clear(record)
        brpm = tracker.get_brpm("forest_1")
        idle_rate = tracker.get_idle_rate("forest_1")
        assert idle_rate == pytest.approx(brpm * IDLE_EFFICIENCY_RATE)
        assert idle_rate == pytest.approx(0.85)

    def test_idle_rate_unrecorded_area(self) -> None:
        """Idle rate for unrecorded area returns 0.0."""
        tracker = IdleTracker()
        assert tracker.get_idle_rate("unknown") == 0.0


class TestGetIdleMonstersPerMinute:
    """Tests for IdleTracker.get_idle_monsters_per_minute()."""

    def test_monsters_per_minute_calculation(self) -> None:
        """Monsters per minute = monsters_per_clear * idle_rate."""
        tracker = IdleTracker()
        record = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        tracker.record_clear(record)
        # idle_rate = 0.85 rounds/min, 10 monsters/round = 8.5 monsters/min
        assert tracker.get_idle_monsters_per_minute("forest_1") == pytest.approx(8.5)

    def test_monsters_per_minute_unrecorded(self) -> None:
        """Monsters per minute for unrecorded area is 0.0."""
        tracker = IdleTracker()
        assert tracker.get_idle_monsters_per_minute("unknown") == 0.0


class TestMultipleAreas:
    """Tests for tracking multiple areas independently."""

    def test_areas_tracked_independently(self) -> None:
        """Different areas maintain separate best times and BRPM."""
        tracker = IdleTracker()
        forest = AreaClearRecord(
            area_id="forest_1",
            clear_time_seconds=60.0,
            monsters_defeated=10,
            timestamp=1000.0,
        )
        cave = AreaClearRecord(
            area_id="cave_1",
            clear_time_seconds=30.0,
            monsters_defeated=5,
            timestamp=1000.0,
        )
        tracker.record_clear(forest)
        tracker.record_clear(cave)

        assert tracker.get_brpm("forest_1") == pytest.approx(1.0)
        assert tracker.get_brpm("cave_1") == pytest.approx(2.0)
        assert tracker.best_monsters_per_clear["forest_1"] == 10
        assert tracker.best_monsters_per_clear["cave_1"] == 5
