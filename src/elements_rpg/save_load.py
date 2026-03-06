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

SAVE_FORMAT_VERSION = 2

# Mapping of old v1 element values to new v2 element values.
# In v1, elements were: fire, water, earth, wind, neutral.
# In v2, elements are: water, fire, grass, electric, wind, ground, rock, dark, light, ice.
_V1_ELEMENT_MIGRATION: dict[str, str] = {
    "earth": "grass",
    "neutral": "dark",
    # fire, water, wind remain unchanged
}


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
    """Deserialize game save from JSON string.

    Automatically detects save version and applies migrations if needed.
    """
    data = json.loads(json_str)
    data = _apply_migrations(data)
    return GameSaveData.model_validate(data)


def save_to_dict(save_data: GameSaveData) -> dict[str, Any]:
    """Convert save data to a dictionary (for cloud storage APIs)."""
    return save_data.model_dump()


def load_from_dict(data: dict[str, Any]) -> GameSaveData:
    """Load save data from a dictionary.

    Automatically detects save version and applies migrations if needed.
    """
    data = _apply_migrations(data)
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


# ---------------------------------------------------------------------------
# Migration logic
# ---------------------------------------------------------------------------


def _apply_migrations(data: dict[str, Any]) -> dict[str, Any]:
    """Apply all necessary migrations to bring data to the current version.

    Args:
        data: Raw save data dict (possibly from an older version).

    Returns:
        Migrated data dict at the current SAVE_FORMAT_VERSION.
    """
    version = data.get("version", 1)

    if version < 2:
        data = _migrate_v1_to_v2(data)

    return data


def _migrate_v1_to_v2(data: dict[str, Any]) -> dict[str, Any]:
    """Migrate a v1 save to v2 format.

    V1 -> V2 changes:
    - Element enum expanded from 5 to 10 values.
    - MonsterSpecies gained `types` tuple field (replacing single `element`).
    - Old element values remapped: earth -> grass, neutral -> dark.

    The save embeds full MonsterSpecies in each Monster. We need to:
    1. Migrate element values in the embedded species data.
    2. Convert the old `element` field to the new `types` tuple format
       if the species data uses the old single-element format.
    """
    monsters = data.get("monsters", [])
    for monster in monsters:
        species = monster.get("species", {})
        _migrate_species_elements(species)

    data["version"] = 2
    return data


def _migrate_element_value(element_str: str) -> str:
    """Map a v1 element string to its v2 equivalent.

    Args:
        element_str: The old element value (e.g., "earth", "neutral", "fire").

    Returns:
        The new element value (e.g., "grass", "dark", "fire").
    """
    return _V1_ELEMENT_MIGRATION.get(element_str, element_str)


def _migrate_species_elements(species: dict[str, Any]) -> None:
    """Migrate element fields in an embedded MonsterSpecies dict in-place.

    Handles two cases:
    1. Old format with `element` field but no `types` field.
    2. Existing `types` field with old element values that need remapping.
    """
    if not species:
        return

    # Case 1: Old format has `element` but no `types` -- convert to types tuple
    if "element" in species and "types" not in species:
        old_element = species.pop("element")
        new_element = _migrate_element_value(old_element)
        species["types"] = [new_element, None]

    # Case 2: Has `types` field -- remap any old element values within it
    if "types" in species:
        types_val = species["types"]
        if isinstance(types_val, (list, tuple)):
            migrated = []
            for t in types_val:
                if isinstance(t, str):
                    migrated.append(_migrate_element_value(t))
                else:
                    migrated.append(t)
            species["types"] = migrated
