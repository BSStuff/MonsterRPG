"""Tests for the main entry point and Player model."""

import pytest
from pydantic import ValidationError

from elements_rpg.combat.strategy import StrategyProfile, StrategyType
from elements_rpg.config import BASE_ACTION_QUEUE_SLOTS
from elements_rpg.main import main
from elements_rpg.player import Player


def test_main_exists() -> None:
    """Verify the main function exists and is callable."""
    assert callable(main)


def _make_player(**overrides: object) -> Player:
    """Create a Player with sensible defaults."""
    defaults: dict[str, object] = {
        "player_id": "player_001",
        "username": "TestHero",
    }
    defaults.update(overrides)
    return Player(**defaults)


class TestPlayer:
    """Tests for Player model."""

    def test_valid_construction(self) -> None:
        """Player should accept valid data."""
        player = _make_player()
        assert player.player_id == "player_001"
        assert player.username == "TestHero"

    def test_empty_player_id_rejected(self) -> None:
        """player_id cannot be empty."""
        with pytest.raises(ValidationError):
            _make_player(player_id="")

    def test_defaults(self) -> None:
        """Default values should be applied correctly."""
        player = _make_player()
        assert player.level == 1
        assert player.experience == 0
        assert player.team_monster_ids == []
        assert player.owned_monster_ids == []
        assert player.active_area_id is None
        assert player.strategy_profiles == []
        assert player.action_queue_slots == BASE_ACTION_QUEUE_SLOTS

    def test_empty_username_rejected(self) -> None:
        """Username cannot be empty."""
        with pytest.raises(ValidationError):
            _make_player(username="")

    def test_long_username_rejected(self) -> None:
        """Username cannot exceed 30 characters."""
        with pytest.raises(ValidationError):
            _make_player(username="A" * 31)

    def test_negative_experience_rejected(self) -> None:
        """Experience cannot be negative."""
        with pytest.raises(ValidationError):
            _make_player(experience=-1)

    def test_max_team_size(self) -> None:
        """Cannot have more than 6 monsters on the team."""
        with pytest.raises(ValidationError):
            _make_player(
                team_monster_ids=["m1", "m2", "m3", "m4", "m5", "m6", "m7"],
            )

    def test_active_area(self) -> None:
        """Player can have an active area."""
        player = _make_player(active_area_id="area_forest")
        assert player.active_area_id == "area_forest"

    def test_strategy_profiles(self) -> None:
        """Player can have strategy profiles."""
        profiles = [
            StrategyProfile(strategy=StrategyType.AGGRESSIVE),
            StrategyProfile(strategy=StrategyType.DEFENSIVE, proficiency_level=5),
        ]
        player = _make_player(strategy_profiles=profiles)
        assert len(player.strategy_profiles) == 2
        assert player.strategy_profiles[1].proficiency_level == 5

    def test_action_queue_slots_bounds(self) -> None:
        """Action queue slots must be between 1 and 10."""
        with pytest.raises(ValidationError):
            _make_player(action_queue_slots=0)
        with pytest.raises(ValidationError):
            _make_player(action_queue_slots=11)

    def test_level_must_be_positive(self) -> None:
        """Player level must be at least 1."""
        with pytest.raises(ValidationError):
            _make_player(level=0)
