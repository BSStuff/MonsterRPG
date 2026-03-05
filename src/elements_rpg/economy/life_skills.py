"""Life skills system — Mining, Cooking, Strategy Training."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class LifeSkillType(StrEnum):
    """The 3 MVP life skills."""

    MINING = "mining"
    COOKING = "cooking"
    STRATEGY_TRAINING = "strategy_training"


class ResourceYield(BaseModel):
    """Result of performing a life skill action."""

    resource_id: str = Field(min_length=1)
    resource_name: str = Field(min_length=1)
    quantity: int = Field(ge=1)
    bonus_quantity: int = Field(default=0, ge=0, description="Extra from skill level")


def life_skill_xp_for_level(level: int) -> int:
    """XP required to advance from current level to next level.

    Formula: int(75 * (level ** 1.4))
    Level 1 = 0 (starting level).
    """
    if level <= 1:
        return 0
    return int(75 * (level**1.4))


class LifeSkill(BaseModel):
    """A player's progression in a specific life skill."""

    skill_type: LifeSkillType
    level: int = Field(default=1, ge=1, le=99)
    experience: int = Field(default=0, ge=0)

    def gain_experience(self, xp: int) -> list[int]:
        """Add XP and handle level-ups. Returns list of new levels gained."""
        if xp <= 0:
            raise ValueError("XP must be positive")
        self.experience += xp
        levels_gained: list[int] = []
        while self.level < 99:
            xp_needed = life_skill_xp_for_level(self.level + 1)
            if self.experience < xp_needed:
                break
            self.experience -= xp_needed
            self.level += 1
            levels_gained.append(self.level)
        return levels_gained

    def resource_bonus(self) -> float:
        """Bonus resource yield multiplier from skill level.

        1% bonus per level above 1. Level 50 = 49% bonus.
        """
        return 1.0 + (self.level - 1) * 0.01

    def speed_bonus(self) -> float:
        """Speed multiplier for action completion.

        0.5% faster per level above 1. Level 50 = 24.5% faster.
        """
        return max(1.0 - (self.level - 1) * 0.005, 0.1)


class LifeSkillAction(BaseModel):
    """Definition of a life skill action (e.g., Mine Iron Ore, Cook Steak)."""

    action_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=50)
    skill_type: LifeSkillType
    required_level: int = Field(default=1, ge=1, le=99)
    base_duration_seconds: float = Field(gt=0)
    xp_reward: int = Field(ge=1)
    resource_yields: list[ResourceYield] = Field(default_factory=list)
    required_materials: dict[str, int] = Field(
        default_factory=dict,
        description="resource_id -> quantity required",
    )

    @model_validator(mode="after")
    def validate_material_quantities(self) -> "LifeSkillAction":
        """Ensure all required material quantities are >= 1."""
        for mat_id, qty in self.required_materials.items():
            if qty < 1:
                raise ValueError(f"Material '{mat_id}' quantity must be >= 1, got {qty}")
        return self


def calculate_action_duration(
    action: LifeSkillAction,
    skill: LifeSkill,
) -> float:
    """Calculate actual duration of a life skill action.

    Args:
        action: The action being performed.
        skill: The player's skill level.

    Returns:
        Duration in seconds, minimum 1.0.
    """
    duration = action.base_duration_seconds * skill.speed_bonus()
    return max(duration, 1.0)


def calculate_resource_yield(
    action: LifeSkillAction,
    skill: LifeSkill,
) -> list[ResourceYield]:
    """Calculate actual resource yields with skill level bonus.

    Args:
        action: The action being performed.
        skill: The player's skill level.

    Returns:
        List of ResourceYield with bonus quantities applied.
    """
    results: list[ResourceYield] = []
    bonus_mult = skill.resource_bonus()
    for base_yield in action.resource_yields:
        total = int(base_yield.quantity * bonus_mult)
        bonus = total - base_yield.quantity
        results.append(
            ResourceYield(
                resource_id=base_yield.resource_id,
                resource_name=base_yield.resource_name,
                quantity=base_yield.quantity,
                bonus_quantity=max(bonus, 0),
            )
        )
    return results
