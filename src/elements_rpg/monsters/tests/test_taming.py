"""Tests for the taming system."""

import pytest
from pydantic import ValidationError

from elements_rpg.config import (
    TAMING_PITY_BONUS_PER_ATTEMPT,
    TAMING_SOFT_PITY_THRESHOLD,
)
from elements_rpg.monsters.models import Rarity
from elements_rpg.monsters.taming import (
    BASE_CAPTURE_RATES,
    FoodItem,
    TamingTracker,
    attempt_tame,
    calculate_pity_bonus,
    calculate_tame_chance,
)

# ---------------------------------------------------------------------------
# BASE_CAPTURE_RATES tests
# ---------------------------------------------------------------------------


class TestBaseCaptureRates:
    """Tests for BASE_CAPTURE_RATES constants."""

    def test_all_rarities_present(self) -> None:
        """All 5 rarity tiers have a base rate."""
        for rarity in Rarity:
            assert rarity in BASE_CAPTURE_RATES

    def test_rates_decrease_with_rarity(self) -> None:
        """Higher rarity = lower base capture rate."""
        assert BASE_CAPTURE_RATES[Rarity.COMMON] > BASE_CAPTURE_RATES[Rarity.UNCOMMON]
        assert BASE_CAPTURE_RATES[Rarity.UNCOMMON] > BASE_CAPTURE_RATES[Rarity.RARE]
        assert BASE_CAPTURE_RATES[Rarity.RARE] > BASE_CAPTURE_RATES[Rarity.EPIC]
        assert BASE_CAPTURE_RATES[Rarity.EPIC] > BASE_CAPTURE_RATES[Rarity.LEGENDARY]

    def test_rates_are_between_zero_and_one(self) -> None:
        """All rates are valid probabilities."""
        for rate in BASE_CAPTURE_RATES.values():
            assert 0.0 < rate <= 1.0


# ---------------------------------------------------------------------------
# Pity system tests
# ---------------------------------------------------------------------------


class TestCalculatePityBonus:
    """Tests for calculate_pity_bonus."""

    def test_zero_attempts(self) -> None:
        """No pity bonus with zero attempts."""
        assert calculate_pity_bonus(0) == 0.0

    def test_below_threshold(self) -> None:
        """No pity bonus below threshold (49 attempts)."""
        assert calculate_pity_bonus(49) == 0.0

    def test_at_threshold(self) -> None:
        """No pity bonus at exactly the threshold (50 attempts)."""
        assert calculate_pity_bonus(TAMING_SOFT_PITY_THRESHOLD) == 0.0

    def test_one_above_threshold(self) -> None:
        """Pity bonus starts one attempt above threshold."""
        bonus = calculate_pity_bonus(TAMING_SOFT_PITY_THRESHOLD + 1)
        assert bonus == pytest.approx(TAMING_PITY_BONUS_PER_ATTEMPT)

    def test_ten_above_threshold(self) -> None:
        """Pity bonus at 60 attempts (10 above threshold)."""
        bonus = calculate_pity_bonus(TAMING_SOFT_PITY_THRESHOLD + 10)
        assert bonus == pytest.approx(10 * TAMING_PITY_BONUS_PER_ATTEMPT)

    def test_fifty_above_threshold(self) -> None:
        """Pity bonus at 100 attempts (50 above threshold)."""
        bonus = calculate_pity_bonus(TAMING_SOFT_PITY_THRESHOLD + 50)
        assert bonus == pytest.approx(50 * TAMING_PITY_BONUS_PER_ATTEMPT)

    def test_pity_scales_linearly(self) -> None:
        """Verify linear scaling of pity bonus."""
        bonus_51 = calculate_pity_bonus(51)
        bonus_52 = calculate_pity_bonus(52)
        bonus_53 = calculate_pity_bonus(53)
        diff_1 = bonus_52 - bonus_51
        diff_2 = bonus_53 - bonus_52
        assert diff_1 == pytest.approx(diff_2)
        assert diff_1 == pytest.approx(TAMING_PITY_BONUS_PER_ATTEMPT)


# ---------------------------------------------------------------------------
# Tame chance calculation tests
# ---------------------------------------------------------------------------


class TestCalculateTameChance:
    """Tests for calculate_tame_chance."""

    def test_no_bonuses_common(self) -> None:
        """Common monster with no bonuses returns base rate."""
        chance = calculate_tame_chance(Rarity.COMMON)
        assert chance == pytest.approx(0.40)

    def test_no_bonuses_uncommon(self) -> None:
        """Uncommon monster with no bonuses returns base rate."""
        chance = calculate_tame_chance(Rarity.UNCOMMON)
        assert chance == pytest.approx(0.25)

    def test_no_bonuses_rare(self) -> None:
        """Rare monster with no bonuses returns base rate."""
        chance = calculate_tame_chance(Rarity.RARE)
        assert chance == pytest.approx(0.12)

    def test_no_bonuses_epic(self) -> None:
        """Epic monster with no bonuses returns base rate."""
        chance = calculate_tame_chance(Rarity.EPIC)
        assert chance == pytest.approx(0.05)

    def test_no_bonuses_legendary(self) -> None:
        """Legendary monster with no bonuses returns base rate."""
        chance = calculate_tame_chance(Rarity.LEGENDARY)
        assert chance == pytest.approx(0.02)

    def test_food_bonus_increases_chance(self) -> None:
        """Food bonus multiplies the base rate."""
        base = calculate_tame_chance(Rarity.COMMON)
        with_food = calculate_tame_chance(Rarity.COMMON, food_bonus=0.5)
        assert with_food > base
        # base_rate * (1 + 0.5) = 0.40 * 1.5 = 0.60
        assert with_food == pytest.approx(0.60)

    def test_skill_bonus_increases_chance(self) -> None:
        """Skill bonus multiplies the base rate."""
        base = calculate_tame_chance(Rarity.RARE)
        with_skill = calculate_tame_chance(Rarity.RARE, skill_bonus=0.3)
        assert with_skill > base
        # 0.12 * (1 + 0.3) = 0.12 * 1.3 = 0.156
        assert with_skill == pytest.approx(0.156)

    def test_chance_capped_at_one(self) -> None:
        """Final chance never exceeds 1.0."""
        chance = calculate_tame_chance(
            Rarity.COMMON,
            food_bonus=1.0,
            skill_bonus=1.0,
            pity_bonus=1.0,
        )
        assert chance == 1.0

    def test_hp_full_no_bonus(self) -> None:
        """Full HP gives no HP modifier."""
        chance_full = calculate_tame_chance(Rarity.COMMON, monster_hp_percent=1.0)
        chance_default = calculate_tame_chance(Rarity.COMMON)
        assert chance_full == pytest.approx(chance_default)

    def test_hp_half_gives_bonus(self) -> None:
        """HP at 50% gives 0.15 modifier."""
        chance = calculate_tame_chance(Rarity.COMMON, monster_hp_percent=0.50)
        # 0.40 * (1 + 0.15) = 0.40 * 1.15 = 0.46
        assert chance == pytest.approx(0.46)

    def test_hp_quarter_gives_bigger_bonus(self) -> None:
        """HP at 25% gives 0.3 modifier."""
        chance = calculate_tame_chance(Rarity.COMMON, monster_hp_percent=0.25)
        # 0.40 * (1 + 0.3) = 0.40 * 1.3 = 0.52
        assert chance == pytest.approx(0.52)

    def test_hp_below_quarter(self) -> None:
        """HP below 25% still gives 0.3 modifier."""
        chance = calculate_tame_chance(Rarity.COMMON, monster_hp_percent=0.10)
        assert chance == pytest.approx(0.52)

    def test_combined_bonuses_stack(self) -> None:
        """All bonuses stack multiplicatively with base, pity is additive."""
        chance = calculate_tame_chance(
            Rarity.RARE,
            food_bonus=0.2,
            skill_bonus=0.1,
            pity_bonus=0.05,
            monster_hp_percent=0.25,
        )
        # 0.12 * (1 + 0.2 + 0.1 + 0.3) + 0.05 = 0.12 * 1.6 + 0.05 = 0.192 + 0.05 = 0.242
        assert chance == pytest.approx(0.242)

    def test_pity_bonus_additive(self) -> None:
        """Pity bonus is added after multiplication."""
        no_pity = calculate_tame_chance(Rarity.LEGENDARY)
        with_pity = calculate_tame_chance(Rarity.LEGENDARY, pity_bonus=0.10)
        assert with_pity == pytest.approx(no_pity + 0.10)


# ---------------------------------------------------------------------------
# TamingTracker tests
# ---------------------------------------------------------------------------


class TestTamingTracker:
    """Tests for TamingTracker."""

    def test_initial_attempts_zero(self) -> None:
        """New tracker returns 0 attempts for any species."""
        tracker = TamingTracker()
        assert tracker.get_attempts("goblin") == 0

    def test_record_failure_increments(self) -> None:
        """record_failure increments the counter and returns new count."""
        tracker = TamingTracker()
        assert tracker.record_failure("goblin") == 1
        assert tracker.record_failure("goblin") == 2
        assert tracker.record_failure("goblin") == 3
        assert tracker.get_attempts("goblin") == 3

    def test_record_success_resets(self) -> None:
        """record_success resets the counter to 0."""
        tracker = TamingTracker()
        tracker.record_failure("goblin")
        tracker.record_failure("goblin")
        tracker.record_success("goblin")
        assert tracker.get_attempts("goblin") == 0

    def test_multiple_species_independent(self) -> None:
        """Different species are tracked independently."""
        tracker = TamingTracker()
        tracker.record_failure("goblin")
        tracker.record_failure("goblin")
        tracker.record_failure("dragon")
        assert tracker.get_attempts("goblin") == 2
        assert tracker.get_attempts("dragon") == 1

    def test_success_on_untracked_species(self) -> None:
        """record_success on untracked species is a no-op."""
        tracker = TamingTracker()
        tracker.record_success("goblin")  # Should not raise
        assert tracker.get_attempts("goblin") == 0


# ---------------------------------------------------------------------------
# FoodItem tests
# ---------------------------------------------------------------------------


class TestFoodItem:
    """Tests for FoodItem model."""

    def test_valid_construction(self) -> None:
        """Valid FoodItem creation."""
        food = FoodItem(food_id="berry_01", name="Sweet Berry", taming_bonus=0.15)
        assert food.food_id == "berry_01"
        assert food.name == "Sweet Berry"
        assert food.taming_bonus == 0.15
        assert food.favorite_for_elements == []
        assert food.favorite_bonus == 0.1

    def test_with_favorite_elements(self) -> None:
        """FoodItem with favorite elements."""
        food = FoodItem(
            food_id="fire_pepper",
            name="Fire Pepper",
            taming_bonus=0.2,
            favorite_for_elements=["fire"],
            favorite_bonus=0.15,
        )
        assert food.favorite_for_elements == ["fire"]
        assert food.favorite_bonus == 0.15

    def test_taming_bonus_too_high(self) -> None:
        """taming_bonus > 1.0 rejected."""
        with pytest.raises(ValidationError):
            FoodItem(food_id="op_food", name="OP Food", taming_bonus=1.5)

    def test_taming_bonus_negative(self) -> None:
        """Negative taming_bonus rejected."""
        with pytest.raises(ValidationError):
            FoodItem(food_id="bad_food", name="Bad Food", taming_bonus=-0.1)

    def test_empty_food_id_rejected(self) -> None:
        """Empty food_id rejected."""
        with pytest.raises(ValidationError):
            FoodItem(food_id="", name="Some Food", taming_bonus=0.1)

    def test_favorite_bonus_range(self) -> None:
        """favorite_bonus > 0.5 rejected."""
        with pytest.raises(ValidationError):
            FoodItem(food_id="f1", name="Food", taming_bonus=0.1, favorite_bonus=0.6)


# ---------------------------------------------------------------------------
# attempt_tame integration tests
# ---------------------------------------------------------------------------


class TestAttemptTame:
    """Integration tests for attempt_tame."""

    def test_successful_tame(self) -> None:
        """Roll below chance = success."""
        tracker = TamingTracker()
        result = attempt_tame(
            rarity=Rarity.COMMON,
            species_id="goblin",
            tracker=tracker,
            roll=0.10,  # well below 0.40 base rate
        )
        assert result.success is True
        assert result.final_chance == pytest.approx(0.40)
        assert tracker.get_attempts("goblin") == 0  # reset on success

    def test_failed_tame(self) -> None:
        """Roll above chance = failure."""
        tracker = TamingTracker()
        result = attempt_tame(
            rarity=Rarity.COMMON,
            species_id="goblin",
            tracker=tracker,
            roll=0.50,  # above 0.40 base rate
        )
        assert result.success is False
        assert tracker.get_attempts("goblin") == 1

    def test_roll_equal_to_chance_succeeds(self) -> None:
        """Roll exactly equal to chance = success (<=)."""
        tracker = TamingTracker()
        result = attempt_tame(
            rarity=Rarity.COMMON,
            species_id="goblin",
            tracker=tracker,
            roll=0.40,  # exactly equal
        )
        assert result.success is True

    def test_pity_accumulates_on_failures(self) -> None:
        """Pity bonus builds up over consecutive failures."""
        tracker = TamingTracker()
        # Simulate 51 failures (just above threshold)
        for _ in range(TAMING_SOFT_PITY_THRESHOLD):
            tracker.record_failure("dragon")

        # 50 failures = at threshold, no pity yet
        result = attempt_tame(
            rarity=Rarity.LEGENDARY,
            species_id="dragon",
            tracker=tracker,
            roll=1.0,  # force failure
        )
        assert result.pity_bonus == 0.0

        # Now at 51 failures, next attempt should have pity
        result = attempt_tame(
            rarity=Rarity.LEGENDARY,
            species_id="dragon",
            tracker=tracker,
            roll=1.0,  # force failure
        )
        assert result.pity_bonus == pytest.approx(TAMING_PITY_BONUS_PER_ATTEMPT)

    def test_success_resets_pity(self) -> None:
        """Success resets pity counter."""
        tracker = TamingTracker()
        for _ in range(55):
            tracker.record_failure("dragon")

        # Force success
        attempt_tame(
            rarity=Rarity.LEGENDARY,
            species_id="dragon",
            tracker=tracker,
            roll=0.0,  # guaranteed success
        )
        assert tracker.get_attempts("dragon") == 0

        # Next attempt should have no pity
        result = attempt_tame(
            rarity=Rarity.LEGENDARY,
            species_id="dragon",
            tracker=tracker,
            roll=1.0,
        )
        assert result.pity_bonus == 0.0

    def test_attempt_fields_populated(self) -> None:
        """TamingAttempt has all fields correctly populated."""
        tracker = TamingTracker()
        result = attempt_tame(
            rarity=Rarity.RARE,
            species_id="wolf",
            tracker=tracker,
            roll=0.05,
            food_bonus=0.2,
            skill_bonus=0.1,
            monster_hp_percent=0.5,
        )
        assert result.monster_species_id == "wolf"
        assert result.attempt_number == 1
        assert result.base_rate == pytest.approx(0.12)
        assert result.food_bonus == pytest.approx(0.2)
        assert result.skill_bonus == pytest.approx(0.1)
        assert result.pity_bonus == 0.0
        # 0.12 * (1 + 0.2 + 0.1 + 0.15) = 0.12 * 1.45 = 0.174
        assert result.final_chance == pytest.approx(0.174)
        assert result.success is True

    def test_attempt_number_increments(self) -> None:
        """attempt_number reflects the attempt count."""
        tracker = TamingTracker()
        r1 = attempt_tame(Rarity.EPIC, "boss", tracker, roll=1.0)
        r2 = attempt_tame(Rarity.EPIC, "boss", tracker, roll=1.0)
        r3 = attempt_tame(Rarity.EPIC, "boss", tracker, roll=1.0)
        assert r1.attempt_number == 1
        assert r2.attempt_number == 2
        assert r3.attempt_number == 3

    def test_food_bonus_applied(self) -> None:
        """Food bonus increases the final chance."""
        tracker = TamingTracker()
        no_food = attempt_tame(Rarity.RARE, "wolf", tracker, roll=1.0)
        tracker_2 = TamingTracker()
        with_food = attempt_tame(Rarity.RARE, "wolf", tracker_2, roll=1.0, food_bonus=0.5)
        assert with_food.final_chance > no_food.final_chance
