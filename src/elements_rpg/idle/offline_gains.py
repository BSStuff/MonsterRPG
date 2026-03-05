"""Offline gains calculation — rewards for time spent offline."""

from pydantic import BaseModel, Field

from elements_rpg.config import OFFLINE_CAP_HOURS
from elements_rpg.idle.tracker import IdleTracker


class OfflineGainsResult(BaseModel):
    """Result of calculating offline gains for a player."""

    area_id: str = Field(min_length=1)
    offline_duration_hours: float = Field(ge=0)
    capped_duration_hours: float = Field(ge=0)
    idle_rate: float = Field(ge=0, description="Rounds per minute")
    total_rounds: int = Field(ge=0)
    estimated_monsters_defeated: int = Field(ge=0)
    estimated_xp: int = Field(ge=0)
    estimated_gold: int = Field(ge=0)
    was_capped: bool


def calculate_offline_gains(
    tracker: IdleTracker,
    area_id: str,
    offline_duration_hours: float,
    offline_cap_hours: float = OFFLINE_CAP_HOURS,
    xp_per_monster: int = 10,
    gold_per_monster: int = 5,
) -> OfflineGainsResult:
    """
    Calculate gains accumulated while offline.

    Formula: capped_duration * idle_rate * 60 = total_rounds

    Args:
        tracker: The player's idle tracker with recorded clear times.
        area_id: The area the player was idling in.
        offline_duration_hours: How long the player was offline.
        offline_cap_hours: Maximum offline hours (default 8).
        xp_per_monster: Base XP per monster defeated.
        gold_per_monster: Base gold per monster defeated.

    Returns:
        OfflineGainsResult with calculated rewards.
    """
    if offline_duration_hours <= 0:
        return OfflineGainsResult(
            area_id=area_id,
            offline_duration_hours=0,
            capped_duration_hours=0,
            idle_rate=0,
            total_rounds=0,
            estimated_monsters_defeated=0,
            estimated_xp=0,
            estimated_gold=0,
            was_capped=False,
        )

    capped = min(offline_duration_hours, offline_cap_hours)
    was_capped = offline_duration_hours > offline_cap_hours

    idle_rate = tracker.get_idle_rate(area_id)
    monsters_per_min = tracker.get_idle_monsters_per_minute(area_id)

    total_minutes = capped * 60.0
    total_rounds = int(idle_rate * total_minutes)
    total_monsters = int(monsters_per_min * total_minutes)

    return OfflineGainsResult(
        area_id=area_id,
        offline_duration_hours=offline_duration_hours,
        capped_duration_hours=capped,
        idle_rate=idle_rate,
        total_rounds=total_rounds,
        estimated_monsters_defeated=total_monsters,
        estimated_xp=total_monsters * xp_per_monster,
        estimated_gold=total_monsters * gold_per_monster,
        was_capped=was_capped,
    )
