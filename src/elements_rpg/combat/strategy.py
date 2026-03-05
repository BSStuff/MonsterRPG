"""Combat strategy types and profiles for auto-combat behavior."""

from enum import StrEnum

from pydantic import BaseModel, Field


class StrategyType(StrEnum):
    """The 5 base combat strategies from the PRD.

    Each strategy determines how a monster behaves in auto-combat.
    """

    ATTACK_NEAREST = "attack_nearest"
    FOLLOW_PLAYER = "follow_player"
    DEFENSIVE = "defensive"
    AGGRESSIVE = "aggressive"
    HEAL_LOWEST = "heal_lowest"


def strategy_xp_for_level(level: int) -> int:
    """Calculate total XP needed to reach a given strategy proficiency level.

    Uses formula: int(200 * (level ** 1.2)). Level 1 requires 0 XP.

    Args:
        level: The target proficiency level (1-10).

    Returns:
        XP required to reach that level.

    Raises:
        ValueError: If level is outside 1-10.
    """
    if level < 1 or level > 10:
        raise ValueError(f"Strategy proficiency level must be 1-10, got {level}")
    if level == 1:
        return 0
    return int(200 * (level**1.2))


class StrategyProfile(BaseModel):
    """A player's proficiency with a specific strategy.

    Attributes:
        strategy: The strategy type.
        proficiency_level: Current proficiency (1-10).
        experience: Accumulated strategy XP.
        is_mastered: Whether the strategy is fully mastered.
        training_time_hours: Total hours spent training this strategy.
    """

    strategy: StrategyType
    proficiency_level: int = Field(default=1, ge=1, le=10)
    experience: int = Field(default=0, ge=0)
    is_mastered: bool = Field(default=False)
    training_time_hours: float = Field(default=0.0, ge=0.0)

    def gain_experience(self, xp: int) -> list[int]:
        """Add XP and process proficiency level-ups.

        Can gain multiple levels at once. Leftover XP is retained.
        Max proficiency level is 10; no XP is added at max.

        Args:
            xp: Amount of XP to add (must be >= 0).

        Returns:
            List of new proficiency levels gained.

        Raises:
            ValueError: If xp is negative.
        """
        if xp < 0:
            raise ValueError(f"XP must be non-negative, got {xp}")

        if self.proficiency_level >= 10:
            return []

        self.experience += xp
        levels_gained: list[int] = []

        while self.proficiency_level < 10:
            next_level = self.proficiency_level + 1
            xp_needed = strategy_xp_for_level(next_level)
            if self.experience >= xp_needed:
                self.proficiency_level = next_level
                self.experience -= xp_needed
                levels_gained.append(next_level)
            else:
                break

        # Cap XP at max level
        if self.proficiency_level >= 10:
            self.experience = 0
            self.is_mastered = True

        return levels_gained

    def check_mastery(self) -> bool:
        """Check and set mastery status.

        Returns:
            True if proficiency_level >= 10 (mastered).
        """
        if self.proficiency_level >= 10:
            self.is_mastered = True
        return self.is_mastered
