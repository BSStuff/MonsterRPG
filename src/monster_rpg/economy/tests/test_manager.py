"""Tests for economy manager — Area model."""

import pytest
from pydantic import ValidationError

from monster_rpg.economy.manager import Area, AreaDifficulty


def _make_area(**overrides: object) -> Area:
    """Create an Area with sensible defaults."""
    defaults: dict[str, object] = {
        "area_id": "area_forest",
        "name": "Verdant Forest",
        "difficulty": AreaDifficulty.EASY,
        "recommended_level": 5,
        "description": "A lush forest teeming with low-level monsters.",
    }
    defaults.update(overrides)
    return Area(**defaults)


class TestAreaDifficulty:
    """Tests for AreaDifficulty enum."""

    def test_all_difficulties(self) -> None:
        """All four difficulties should be defined."""
        assert set(AreaDifficulty) == {
            AreaDifficulty.EASY,
            AreaDifficulty.MEDIUM,
            AreaDifficulty.HARD,
            AreaDifficulty.BOSS,
        }

    def test_values(self) -> None:
        """Difficulty values should be lowercase strings."""
        assert AreaDifficulty.EASY.value == "easy"
        assert AreaDifficulty.BOSS.value == "boss"


class TestArea:
    """Tests for Area model."""

    def test_valid_construction(self) -> None:
        """Area should accept valid data."""
        area = _make_area()
        assert area.area_id == "area_forest"
        assert area.name == "Verdant Forest"
        assert area.difficulty == AreaDifficulty.EASY
        assert area.recommended_level == 5

    def test_defaults(self) -> None:
        """Lists should default to empty."""
        area = _make_area()
        assert area.monster_species_ids == []
        assert area.material_drop_ids == []

    def test_with_monsters_and_materials(self) -> None:
        """Area should accept monster and material IDs."""
        area = _make_area(
            monster_species_ids=["sp_1", "sp_2"],
            material_drop_ids=["mat_wood", "mat_stone"],
        )
        assert len(area.monster_species_ids) == 2
        assert len(area.material_drop_ids) == 2

    def test_empty_name_rejected(self) -> None:
        """Name cannot be empty."""
        with pytest.raises(ValidationError):
            _make_area(name="")

    def test_long_name_rejected(self) -> None:
        """Name cannot exceed 50 characters."""
        with pytest.raises(ValidationError):
            _make_area(name="B" * 51)

    def test_recommended_level_bounds(self) -> None:
        """Recommended level must be between 1 and 100."""
        with pytest.raises(ValidationError):
            _make_area(recommended_level=0)
        with pytest.raises(ValidationError):
            _make_area(recommended_level=101)
