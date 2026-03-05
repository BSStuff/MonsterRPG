"""Monster taming system — capture rate calculation with soft pity."""

from pydantic import BaseModel, Field

from elements_rpg.config import (
    TAMING_PITY_BONUS_PER_ATTEMPT,
    TAMING_SOFT_PITY_THRESHOLD,
)
from elements_rpg.monsters.models import Rarity

# Base capture rates by rarity
BASE_CAPTURE_RATES: dict[Rarity, float] = {
    Rarity.COMMON: 0.40,
    Rarity.UNCOMMON: 0.25,
    Rarity.RARE: 0.12,
    Rarity.EPIC: 0.05,
    Rarity.LEGENDARY: 0.02,
}


class FoodItem(BaseModel):
    """A food item that can be used to improve taming chance.

    Attributes:
        food_id: Unique food identifier.
        name: Display name.
        taming_bonus: Additive bonus to tame chance (0.0-1.0).
        favorite_for_elements: Elements this food is especially effective for.
        favorite_bonus: Extra bonus when used on a matching element monster.
    """

    food_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=50)
    taming_bonus: float = Field(ge=0.0, le=1.0, description="Additive bonus to tame chance")
    favorite_for_elements: list[str] = Field(
        default_factory=list,
        description="Elements this food is especially effective for",
    )
    favorite_bonus: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Extra bonus when used on a matching element monster",
    )


class TamingAttempt(BaseModel):
    """Record of a single taming attempt.

    Attributes:
        monster_species_id: Species ID of the monster being tamed.
        attempt_number: Which attempt this was (1-indexed).
        base_rate: Base capture rate for the rarity.
        food_bonus: Bonus from food item.
        skill_bonus: Bonus from player taming skill.
        pity_bonus: Soft pity bonus from failed attempts.
        final_chance: Final calculated tame chance.
        success: Whether the taming succeeded.
    """

    monster_species_id: str = Field(min_length=1)
    attempt_number: int = Field(ge=1)
    base_rate: float = Field(ge=0.0, le=1.0)
    food_bonus: float = Field(default=0.0, ge=0.0)
    skill_bonus: float = Field(default=0.0, ge=0.0)
    pity_bonus: float = Field(default=0.0, ge=0.0)
    final_chance: float = Field(ge=0.0, le=1.0)
    success: bool


class TamingTracker(BaseModel):
    """Tracks taming attempts per species for soft pity calculation.

    Attributes:
        attempts_per_species: Map of species_id to consecutive failed attempts.
    """

    attempts_per_species: dict[str, int] = Field(default_factory=dict)

    def get_attempts(self, species_id: str) -> int:
        """Get number of failed attempts for a species."""
        return self.attempts_per_species.get(species_id, 0)

    def record_failure(self, species_id: str) -> int:
        """Record a failed attempt. Returns new attempt count."""
        current = self.get_attempts(species_id)
        self.attempts_per_species[species_id] = current + 1
        return current + 1

    def record_success(self, species_id: str) -> None:
        """Reset attempt counter on successful tame."""
        self.attempts_per_species.pop(species_id, None)


def calculate_pity_bonus(attempts: int) -> float:
    """Calculate soft pity bonus based on failed attempts.

    Pity kicks in after TAMING_SOFT_PITY_THRESHOLD attempts,
    adding TAMING_PITY_BONUS_PER_ATTEMPT for each attempt beyond threshold.

    Args:
        attempts: Number of consecutive failed attempts.

    Returns:
        Pity bonus (0.0 if below threshold).
    """
    if attempts <= TAMING_SOFT_PITY_THRESHOLD:
        return 0.0
    excess = attempts - TAMING_SOFT_PITY_THRESHOLD
    return excess * TAMING_PITY_BONUS_PER_ATTEMPT


def calculate_tame_chance(
    rarity: Rarity,
    food_bonus: float = 0.0,
    skill_bonus: float = 0.0,
    pity_bonus: float = 0.0,
    monster_hp_percent: float = 1.0,
) -> float:
    """Calculate final taming chance.

    Formula: min(base_rate * (1 + food_bonus + skill_bonus + hp_modifier) + pity_bonus, 1.0)

    HP modifier: lower HP = easier to tame.
    HP < 50% gives bonus, HP < 25% gives bigger bonus.

    Args:
        rarity: Monster rarity tier.
        food_bonus: Bonus from food item (0.0-1.0).
        skill_bonus: Bonus from player taming skill (0.0-1.0).
        pity_bonus: Soft pity bonus from failed attempts.
        monster_hp_percent: Current HP as percentage (0.0-1.0).

    Returns:
        Final tame chance clamped to [0.0, 1.0].
    """
    base_rate = BASE_CAPTURE_RATES.get(rarity, 0.10)

    # HP modifier: lower HP = easier tame
    if monster_hp_percent <= 0.25:
        hp_modifier = 0.3
    elif monster_hp_percent <= 0.50:
        hp_modifier = 0.15
    else:
        hp_modifier = 0.0

    # PRD formula: Base Rate x (modifiers) + pity
    modified_rate = base_rate * (1.0 + food_bonus + skill_bonus + hp_modifier)
    final_chance = modified_rate + pity_bonus

    return max(0.0, min(final_chance, 1.0))


def attempt_tame(
    rarity: Rarity,
    species_id: str,
    tracker: TamingTracker,
    roll: float,
    food_bonus: float = 0.0,
    skill_bonus: float = 0.0,
    monster_hp_percent: float = 1.0,
) -> TamingAttempt:
    """Execute a taming attempt.

    Args:
        rarity: Monster rarity.
        species_id: Monster species ID.
        tracker: Taming tracker for pity calculation.
        roll: Random roll 0.0-1.0 (pass explicitly for deterministic testing).
        food_bonus: Food item bonus.
        skill_bonus: Player taming skill bonus.
        monster_hp_percent: Monster's current HP percentage.

    Returns:
        TamingAttempt with result.
    """
    attempts = tracker.get_attempts(species_id)
    pity = calculate_pity_bonus(attempts)

    chance = calculate_tame_chance(
        rarity=rarity,
        food_bonus=food_bonus,
        skill_bonus=skill_bonus,
        pity_bonus=pity,
        monster_hp_percent=monster_hp_percent,
    )

    success = roll <= chance

    if success:
        tracker.record_success(species_id)
    else:
        tracker.record_failure(species_id)

    return TamingAttempt(
        monster_species_id=species_id,
        attempt_number=attempts + 1,
        base_rate=BASE_CAPTURE_RATES.get(rarity, 0.10),
        food_bonus=food_bonus,
        skill_bonus=skill_bonus,
        pity_bonus=pity,
        final_chance=chance,
        success=success,
    )
