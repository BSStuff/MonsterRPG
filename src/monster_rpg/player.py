"""Player data model — core player state and progression."""

from pydantic import BaseModel, Field

from monster_rpg.combat.damage_calc import StrategyProfile
from monster_rpg.config import BASE_ACTION_QUEUE_SLOTS, MAX_TEAM_SIZE


class Player(BaseModel):
    """Core player data model.

    Attributes:
        player_id: Unique player identifier.
        username: Display name.
        level: Player level.
        experience: Accumulated player XP.
        team_monster_ids: IDs of monsters on the active team (max 6).
        owned_monster_ids: IDs of all owned monsters.
        active_area_id: ID of the area currently being explored.
        gems: Premium currency balance.
        gold: Standard currency balance.
        strategy_profiles: Proficiency data for each strategy.
        action_queue_slots: Number of available action queue slots.
    """

    player_id: str = Field(description="Unique player identifier")
    username: str = Field(min_length=1, max_length=30)
    level: int = Field(default=1, ge=1)
    experience: int = Field(default=0, ge=0)
    team_monster_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_TEAM_SIZE,
    )
    owned_monster_ids: list[str] = Field(default_factory=list)
    active_area_id: str | None = Field(default=None)
    gems: int = Field(default=0, ge=0, description="Premium currency")
    gold: int = Field(default=0, ge=0, description="Standard currency")
    strategy_profiles: list[StrategyProfile] = Field(default_factory=list)
    action_queue_slots: int = Field(
        default=BASE_ACTION_QUEUE_SLOTS,
        ge=1,
        le=5,
    )
