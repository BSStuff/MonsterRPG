"""Save/Load system — cloud-ready serialization of all player data."""

import json
from typing import Any

from pydantic import BaseModel, Field

from elements_rpg.economy.action_queue import ActionQueue
from elements_rpg.economy.crafting import Inventory
from elements_rpg.economy.life_skills import LifeSkill
from elements_rpg.economy.manager import EconomyManager
from elements_rpg.economy.reward_ads import RewardAdTracker
from elements_rpg.economy.subscription import PlayerSubscription
from elements_rpg.idle.tracker import IdleTracker
from elements_rpg.monsters.models import Monster
from elements_rpg.monsters.taming import TamingTracker
from elements_rpg.monsters.team import Team
from elements_rpg.player import Player

SAVE_FORMAT_VERSION = 1


class GameSaveData(BaseModel):
    """Complete game state for serialization."""

    version: int = Field(default=SAVE_FORMAT_VERSION)
    player: Player
    monsters: list[Monster] = Field(default_factory=list)
    teams: list[Team] = Field(default_factory=list)
    inventory: Inventory = Field(default_factory=Inventory)
    economy: EconomyManager = Field(default_factory=EconomyManager)
    idle_tracker: IdleTracker = Field(default_factory=IdleTracker)
    taming_tracker: TamingTracker = Field(default_factory=TamingTracker)
    action_queue: ActionQueue = Field(default_factory=ActionQueue)
    life_skills: list[LifeSkill] = Field(default_factory=list)
    subscription: PlayerSubscription = Field(default_factory=PlayerSubscription)
    ad_tracker: RewardAdTracker = Field(default_factory=RewardAdTracker)
    premium_purchases: dict[str, int] = Field(
        default_factory=dict,
        description="upgrade_id -> purchase count",
    )
    timestamp: float = Field(default=0, ge=0, description="Save timestamp")


def serialize_save(save_data: GameSaveData) -> str:
    """Serialize game save to JSON string."""
    return save_data.model_dump_json(indent=2)


def deserialize_save(json_str: str) -> GameSaveData:
    """Deserialize game save from JSON string."""
    return GameSaveData.model_validate_json(json_str)


def save_to_dict(save_data: GameSaveData) -> dict[str, Any]:
    """Convert save data to a dictionary (for cloud storage APIs)."""
    return save_data.model_dump()


def load_from_dict(data: dict[str, Any]) -> GameSaveData:
    """Load save data from a dictionary."""
    return GameSaveData.model_validate(data)


def create_new_save(
    player_id: str,
    username: str,
) -> GameSaveData:
    """Create a fresh save for a new player."""
    from elements_rpg.economy.life_skills import LifeSkillType

    player = Player(
        player_id=player_id,
        username=username,
    )
    # Initialize all 3 life skills at level 1
    life_skills = [
        LifeSkill(skill_type=LifeSkillType.MINING),
        LifeSkill(skill_type=LifeSkillType.COOKING),
        LifeSkill(skill_type=LifeSkillType.STRATEGY_TRAINING),
    ]
    return GameSaveData(
        player=player,
        life_skills=life_skills,
    )


def validate_save_version(json_str: str) -> int:
    """Check the version of a save file without full deserialization."""
    data = json.loads(json_str)
    return data.get("version", 0)
