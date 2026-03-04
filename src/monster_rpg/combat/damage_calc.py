"""Damage calculation — computes damage based on stats, skills, and modifiers."""

from enum import StrEnum

from pydantic import BaseModel, Field


class StrategyType(StrEnum):
    """The 5 base combat strategies from the PRD.

    Each strategy determines how a monster behaves in auto-combat.
    """

    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    BALANCED = "balanced"
    SUPPORT = "support"
    BOSS_KILLER = "boss_killer"


class StrategyProfile(BaseModel):
    """A player's proficiency with a specific strategy.

    Attributes:
        strategy: The strategy type.
        proficiency_level: Current proficiency (1-10).
        experience: Accumulated strategy XP.
        is_mastered: Whether the strategy is fully mastered.
    """

    strategy: StrategyType
    proficiency_level: int = Field(default=1, ge=1, le=10)
    experience: int = Field(default=0, ge=0)
    is_mastered: bool = Field(default=False)
