"""Skill progression — leveling via usage, milestone upgrades, and XP tracking."""

from enum import StrEnum

from pydantic import BaseModel, Field

from monster_rpg.monsters.models import Element


class SkillType(StrEnum):
    """Categories of skills a monster can use."""

    ATTACK = "attack"
    DEFENSE = "defense"
    SUPPORT = "support"
    SPECIAL = "special"


class Skill(BaseModel):
    """A skill that can be equipped by monsters.

    Attributes:
        skill_id: Unique skill identifier.
        name: Display name of the skill.
        skill_type: Category of the skill.
        element: Elemental affinity of the skill.
        power: Base power value.
        accuracy: Hit chance percentage (1-100).
        cooldown: Cooldown in seconds.
        description: Text description of the skill.
        level: Current skill level (1-20).
        experience: Accumulated skill XP.
    """

    skill_id: str = Field(description="Unique skill identifier")
    name: str = Field(min_length=1, max_length=50)
    skill_type: SkillType
    element: Element
    power: int = Field(ge=0, description="Base power")
    accuracy: int = Field(ge=1, le=100, description="Hit chance percentage")
    cooldown: float = Field(ge=0, description="Cooldown in seconds")
    description: str
    level: int = Field(default=1, ge=1, le=20)
    experience: int = Field(default=0, ge=0)
