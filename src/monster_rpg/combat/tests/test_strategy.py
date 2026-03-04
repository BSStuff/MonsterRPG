"""Tests for strategy types and profiles."""

import pytest
from pydantic import ValidationError

from monster_rpg.combat.strategy import StrategyProfile, StrategyType


def _make_profile(**overrides: object) -> StrategyProfile:
    """Create a StrategyProfile with sensible defaults."""
    defaults: dict[str, object] = {
        "strategy": StrategyType.BALANCED,
    }
    defaults.update(overrides)
    return StrategyProfile(**defaults)


class TestStrategyType:
    """Tests for StrategyType enum."""

    def test_all_strategies(self) -> None:
        """All five strategies should be defined."""
        assert set(StrategyType) == {
            StrategyType.AGGRESSIVE,
            StrategyType.DEFENSIVE,
            StrategyType.BALANCED,
            StrategyType.SUPPORT,
            StrategyType.BOSS_KILLER,
        }

    def test_values(self) -> None:
        """Strategy type values should be lowercase strings."""
        assert StrategyType.AGGRESSIVE.value == "aggressive"
        assert StrategyType.BOSS_KILLER.value == "boss_killer"


class TestStrategyProfile:
    """Tests for StrategyProfile model."""

    def test_valid_construction(self) -> None:
        """StrategyProfile should accept valid data."""
        profile = _make_profile()
        assert profile.strategy == StrategyType.BALANCED

    def test_defaults(self) -> None:
        """Default proficiency should be 1, experience 0, not mastered."""
        profile = _make_profile()
        assert profile.proficiency_level == 1
        assert profile.experience == 0
        assert profile.is_mastered is False

    def test_all_fields(self) -> None:
        """StrategyProfile should accept all fields."""
        profile = _make_profile(
            strategy=StrategyType.AGGRESSIVE,
            proficiency_level=10,
            experience=5000,
            is_mastered=True,
        )
        assert profile.strategy == StrategyType.AGGRESSIVE
        assert profile.proficiency_level == 10
        assert profile.experience == 5000
        assert profile.is_mastered is True

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
