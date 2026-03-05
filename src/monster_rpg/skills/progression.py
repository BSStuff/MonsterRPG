"""Skill progression — leveling via usage, milestone upgrades, and XP tracking."""

from enum import StrEnum

from pydantic import BaseModel, Field

from monster_rpg.config import (
    MAX_SKILL_LEVEL,
    SKILL_LEVEL_COOLDOWN_REDUCTION,
    SKILL_LEVEL_POWER_BONUS,
    SKILL_MIN_COOLDOWN,
)
from monster_rpg.monsters.models import Element


class SkillType(StrEnum):
    """Categories of skills a monster can use."""

    ATTACK = "attack"
    DEFENSE = "defense"
    SUPPORT = "support"
    SPECIAL = "special"


class SkillMilestone(BaseModel):
    """A milestone upgrade unlocked at a specific skill level.

    Attributes:
        level_required: Skill level needed to unlock this milestone.
        name: Display name of the milestone upgrade.
        description: Text description of the upgrade effect.
        bonus_type: Category of bonus (damage, cooldown, aoe_size, buff_duration, proc_chance).
        bonus_value: Numeric bonus value (e.g., 0.1 for 10% bonus).
    """

    level_required: int = Field(ge=1)
    name: str = Field(min_length=1)
    description: str
    bonus_type: str  # e.g., "damage", "cooldown", "aoe_size", "buff_duration", "proc_chance"
    bonus_value: float  # e.g., 0.1 for 10% bonus


def skill_xp_for_level(level: int) -> int:
    """Calculate the total XP needed to reach a given skill level.

    Uses formula: int(50 * (level ** 1.3)). Level 1 requires 0 XP.

    Args:
        level: The target skill level (1 to MAX_SKILL_LEVEL).

    Returns:
        Total XP required to reach that level.

    Raises:
        ValueError: If level is less than 1 or greater than MAX_SKILL_LEVEL.
    """
    if level < 1 or level > MAX_SKILL_LEVEL:
        raise ValueError(f"Skill level must be between 1 and {MAX_SKILL_LEVEL}, got {level}")
    if level == 1:
        return 0
    return int(50 * (level**1.3))


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
        milestones: List of milestone upgrades for this skill.
    """

    skill_id: str = Field(min_length=1, description="Unique skill identifier")
    name: str = Field(min_length=1, max_length=50)
    skill_type: SkillType
    element: Element
    power: int = Field(ge=0, description="Base power")
    accuracy: int = Field(ge=1, le=100, description="Hit chance percentage")
    cooldown: float = Field(ge=0, description="Cooldown in seconds")
    description: str
    level: int = Field(default=1, ge=1, le=MAX_SKILL_LEVEL)
    experience: int = Field(default=0, ge=0)
    milestones: list[SkillMilestone] = Field(default_factory=list)

    def gain_experience(self, xp: int) -> list[int]:
        """Add XP to the skill, handling level-ups up to the max level.

        Leftover XP is retained after leveling. If already at max level,
        no XP is added.

        Args:
            xp: Amount of XP to add (must be positive).

        Returns:
            List of levels gained (e.g., [2, 3] if leveled from 1 to 3).

        Raises:
            ValueError: If xp is not positive.
        """
        if xp <= 0:
            raise ValueError(f"XP must be positive, got {xp}")

        if self.level >= MAX_SKILL_LEVEL:
            return []

        self.experience += xp
        levels_gained: list[int] = []

        while self.level < MAX_SKILL_LEVEL:
            next_level = self.level + 1
            xp_needed = skill_xp_for_level(next_level)
            if self.experience >= xp_needed:
                self.level = next_level
                levels_gained.append(next_level)
            else:
                break

        # Cap XP at max level threshold if at max
        if self.level >= MAX_SKILL_LEVEL:
            self.experience = skill_xp_for_level(MAX_SKILL_LEVEL)

        return levels_gained

    def unlocked_milestones(self) -> list[SkillMilestone]:
        """Return milestones that have been unlocked at the current level.

        Returns:
            List of milestones where level_required <= self.level.
        """
        return [m for m in self.milestones if m.level_required <= self.level]

    def next_milestone(self) -> SkillMilestone | None:
        """Return the next locked milestone, or None if all are unlocked.

        Returns:
            The lowest-level milestone not yet unlocked, or None.
        """
        locked = [m for m in self.milestones if m.level_required > self.level]
        if not locked:
            return None
        return min(locked, key=lambda m: m.level_required)

    def effective_power(self) -> int:
        """Calculate effective power including level bonus.

        Applies a 2% bonus per level above 1 to the base power.

        Returns:
            Effective power as an integer.
        """
        bonus = 1.0 + (self.level - 1) * SKILL_LEVEL_POWER_BONUS
        return int(self.power * bonus)

    def effective_cooldown(self) -> float:
        """Calculate effective cooldown with level-based reduction.

        Reduces cooldown by 1% per level above 1, with a minimum of 0.5 seconds.

        Returns:
            Effective cooldown in seconds (minimum 0.5).
        """
        reduction = 1.0 - (self.level - 1) * SKILL_LEVEL_COOLDOWN_REDUCTION
        return max(self.cooldown * reduction, SKILL_MIN_COOLDOWN)
