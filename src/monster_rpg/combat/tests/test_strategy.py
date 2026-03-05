"""Tests for strategy types, profiles, and progression."""

import pytest
from pydantic import ValidationError

from monster_rpg.combat.strategy import (
    StrategyProfile,
    StrategyType,
    strategy_xp_for_level,
)


def _make_profile(**overrides: object) -> StrategyProfile:
    """Create a StrategyProfile with sensible defaults."""
    defaults: dict[str, object] = {
        "strategy": StrategyType.ATTACK_NEAREST,
    }
    defaults.update(overrides)
    return StrategyProfile(**defaults)


class TestStrategyType:
    """Tests for StrategyType enum."""

    def test_all_strategies(self) -> None:
        """All five PRD strategies should be defined."""
        assert set(StrategyType) == {
            StrategyType.ATTACK_NEAREST,
            StrategyType.FOLLOW_PLAYER,
            StrategyType.DEFENSIVE,
            StrategyType.AGGRESSIVE,
            StrategyType.HEAL_LOWEST,
        }

    def test_values(self) -> None:
        """Strategy type values should be lowercase strings."""
        assert StrategyType.AGGRESSIVE.value == "aggressive"
        assert StrategyType.ATTACK_NEAREST.value == "attack_nearest"
        assert StrategyType.FOLLOW_PLAYER.value == "follow_player"
        assert StrategyType.DEFENSIVE.value == "defensive"
        assert StrategyType.HEAL_LOWEST.value == "heal_lowest"

    def test_strategy_count(self) -> None:
        """Exactly 5 strategies defined per PRD."""
        assert len(StrategyType) == 5


class TestStrategyXpForLevel:
    """Tests for strategy_xp_for_level formula."""

    def test_level_1_requires_zero(self) -> None:
        """Level 1 requires 0 XP."""
        assert strategy_xp_for_level(1) == 0

    def test_level_2_formula(self) -> None:
        """Level 2 uses int(200 * 2^1.2)."""
        assert strategy_xp_for_level(2) == int(200 * (2**1.2))

    def test_level_10_formula(self) -> None:
        """Level 10 uses int(200 * 10^1.2)."""
        assert strategy_xp_for_level(10) == int(200 * (10**1.2))

    def test_invalid_level_zero(self) -> None:
        """Level 0 is invalid."""
        with pytest.raises(ValueError, match="1-10"):
            strategy_xp_for_level(0)

    def test_invalid_level_11(self) -> None:
        """Level 11 is invalid."""
        with pytest.raises(ValueError, match="1-10"):
            strategy_xp_for_level(11)


class TestStrategyProfile:
    """Tests for StrategyProfile model."""

    def test_valid_construction(self) -> None:
        """StrategyProfile should accept valid data."""
        profile = _make_profile()
        assert profile.strategy == StrategyType.ATTACK_NEAREST

    def test_defaults(self) -> None:
        """Default proficiency should be 1, experience 0, not mastered."""
        profile = _make_profile()
        assert profile.proficiency_level == 1
        assert profile.experience == 0
        assert profile.is_mastered is False
        assert profile.training_time_hours == 0.0

    def test_all_fields(self) -> None:
        """StrategyProfile should accept all fields."""
        profile = _make_profile(
            strategy=StrategyType.AGGRESSIVE,
            proficiency_level=10,
            experience=5000,
            is_mastered=True,
            training_time_hours=12.5,
        )
        assert profile.strategy == StrategyType.AGGRESSIVE
        assert profile.proficiency_level == 10
        assert profile.experience == 5000
        assert profile.is_mastered is True
        assert profile.training_time_hours == 12.5

    def test_proficiency_bounds(self) -> None:
        """Proficiency must be between 1 and 10."""
        with pytest.raises(ValidationError):
            _make_profile(proficiency_level=0)
        with pytest.raises(ValidationError):
            _make_profile(proficiency_level=11)

    def test_negative_experience_rejected(self) -> None:
        """Experience cannot be negative."""
        with pytest.raises(ValidationError):
            _make_profile(experience=-1)

    def test_negative_training_time_rejected(self) -> None:
        """Training time cannot be negative."""
        with pytest.raises(ValidationError):
            _make_profile(training_time_hours=-1.0)


class TestStrategyProfileGainExperience:
    """Tests for StrategyProfile.gain_experience method."""

    def test_gain_xp_no_level(self) -> None:
        """Small XP gain should not trigger a level-up."""
        profile = _make_profile()
        levels = profile.gain_experience(10)
        assert levels == []
        assert profile.experience == 10
        assert profile.proficiency_level == 1

    def test_gain_xp_level_up(self) -> None:
        """Enough XP should trigger a level-up."""
        profile = _make_profile()
        xp_needed = strategy_xp_for_level(2)
        levels = profile.gain_experience(xp_needed)
        assert 2 in levels
        assert profile.proficiency_level == 2

    def test_gain_xp_multi_level(self) -> None:
        """Large XP dump should trigger multiple level-ups."""
        profile = _make_profile()
        # Give a huge amount of XP
        levels = profile.gain_experience(100_000)
        assert len(levels) > 1
        assert profile.proficiency_level > 2

    def test_gain_xp_at_max_level(self) -> None:
        """No XP or levels gained at max level 10."""
        profile = _make_profile(proficiency_level=10)
        levels = profile.gain_experience(1000)
        assert levels == []
        assert profile.proficiency_level == 10

    def test_gain_xp_negative_rejected(self) -> None:
        """Negative XP should raise ValueError."""
        profile = _make_profile()
        with pytest.raises(ValueError, match="non-negative"):
            profile.gain_experience(-1)

    def test_gain_xp_to_max_sets_mastery(self) -> None:
        """Reaching level 10 should auto-set is_mastered."""
        profile = _make_profile()
        profile.gain_experience(1_000_000)
        assert profile.proficiency_level == 10
        assert profile.is_mastered is True
        assert profile.experience == 0

    def test_gain_xp_zero(self) -> None:
        """Zero XP should be accepted without error."""
        profile = _make_profile()
        levels = profile.gain_experience(0)
        assert levels == []
        assert profile.experience == 0


class TestStrategyProfileCheckMastery:
    """Tests for StrategyProfile.check_mastery method."""

    def test_not_mastered_at_low_level(self) -> None:
        """check_mastery returns False when below level 10."""
        profile = _make_profile(proficiency_level=5)
        assert profile.check_mastery() is False
        assert profile.is_mastered is False

    def test_mastered_at_level_10(self) -> None:
        """check_mastery returns True and sets flag at level 10."""
        profile = _make_profile(proficiency_level=10)
        assert profile.check_mastery() is True
        assert profile.is_mastered is True

    def test_mastery_idempotent(self) -> None:
        """Calling check_mastery multiple times is safe."""
        profile = _make_profile(proficiency_level=10)
        profile.check_mastery()
        profile.check_mastery()
        assert profile.is_mastered is True
