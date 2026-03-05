"""Idle system — BRPM tracking and idle rate calculation."""

from pydantic import BaseModel, Field

from monster_rpg.config import IDLE_EFFICIENCY_RATE


class AreaClearRecord(BaseModel):
    """Record of clearing an area."""

    area_id: str = Field(min_length=1)
    clear_time_seconds: float = Field(gt=0, description="Time to clear in seconds")
    monsters_defeated: int = Field(ge=1)
    timestamp: float = Field(ge=0, description="Unix timestamp of clear")


class IdleTracker(BaseModel):
    """
    Tracks idle combat performance per area.

    BRPM = Best Rounds Per Minute (fastest clear time converted to rate).
    Idle Rate = BRPM * IDLE_EFFICIENCY_RATE (85%).
    """

    # Best clear time per area (area_id -> seconds)
    best_clear_times: dict[str, float] = Field(default_factory=dict)
    # Best monsters defeated per clear per area
    best_monsters_per_clear: dict[str, int] = Field(default_factory=dict)

    def record_clear(self, record: AreaClearRecord) -> bool:
        """
        Record an area clear. Updates best time if this is a new record.

        Returns:
            True if this was a new best time.
        """
        current_best = self.best_clear_times.get(record.area_id)
        is_new_best = current_best is None or record.clear_time_seconds < current_best

        if is_new_best:
            self.best_clear_times[record.area_id] = record.clear_time_seconds
            self.best_monsters_per_clear[record.area_id] = record.monsters_defeated

        return is_new_best

    def get_brpm(self, area_id: str) -> float:
        """
        Get Best Rounds Per Minute for an area.

        Returns:
            BRPM, or 0.0 if no clears recorded.
        """
        best_time = self.best_clear_times.get(area_id)
        if best_time is None or best_time <= 0:
            return 0.0
        return 60.0 / best_time  # rounds per minute

    def get_idle_rate(self, area_id: str) -> float:
        """
        Get idle farming rate for an area (85% of BRPM).

        Returns:
            Idle rate in rounds per minute, or 0.0 if no clears.
        """
        return self.get_brpm(area_id) * IDLE_EFFICIENCY_RATE

    def get_idle_monsters_per_minute(self, area_id: str) -> float:
        """
        Get estimated monsters defeated per minute while idling.

        Returns:
            Monsters per minute, or 0.0 if no clears.
        """
        monsters = self.best_monsters_per_clear.get(area_id, 0)
        idle_rate = self.get_idle_rate(area_id)
        return monsters * idle_rate
