"""Tests for monster models."""

import pytest
from pydantic import ValidationError

from monster_rpg.monsters.models import (
    Element,
    Monster,
    MonsterSpecies,
    Rarity,
    StatBlock,
)


def _make_stat_block(**overrides: int) -> StatBlock:
    """Create a StatBlock with sensible defaults."""
    defaults = {
        "hp": 100,
        "attack": 50,
        "defense": 40,
        "speed": 30,
        "magic_attack": 45,
        "magic_defense": 35,
    }
    defaults.update(overrides)
    return StatBlock(**defaults)


def _make_species(**overrides: object) -> MonsterSpecies:
    """Create a MonsterSpecies with sensible defaults."""
    defaults: dict[str, object] = {
        "species_id": "sp_flame_wolf",
        "name": "Flame Wolf",
        "element": Element.FIRE,
        "rarity": Rarity.COMMON,
        "base_stats": _make_stat_block(),
        "passive_trait": "Blaze",
        "passive_description": "Boosts fire damage by 10%",
    }
    defaults.update(overrides)
    return MonsterSpecies(**defaults)


def _make_monster(**overrides: object) -> Monster:
    """Create a Monster with sensible defaults."""
    defaults: dict[str, object] = {
        "monster_id": "mon_001",
        "species": _make_species(),
        "current_hp": 100,
    }
    defaults.update(overrides)
    return Monster(**defaults)


# --- Element enum ---


class TestElement:
    """Tests for Element enum."""

    def test_all_elements(self) -> None:
        """All five elements should be defined."""
        assert set(Element) == {
            Element.FIRE,
            Element.WATER,
            Element.EARTH,
            Element.WIND,
            Element.NEUTRAL,
        }

    def test_element_values(self) -> None:
        """Element values should be lowercase strings."""
        assert Element.FIRE.value == "fire"
        assert Element.NEUTRAL.value == "neutral"


# --- Rarity enum ---


class TestRarity:
    """Tests for Rarity enum."""

    def test_all_rarities(self) -> None:
        """All five rarities should be defined."""
        assert len(Rarity) == 5

    def test_rarity_values(self) -> None:
        """Rarity values should be lowercase strings."""
        assert Rarity.COMMON.value == "common"
        assert Rarity.LEGENDARY.value == "legendary"


# --- StatBlock ---


class TestStatBlock:
    """Tests for StatBlock model."""

    def test_valid_construction(self) -> None:
        """StatBlock should accept valid positive stats."""
        stats = _make_stat_block()
        assert stats.hp == 100
        assert stats.attack == 50

    def test_hp_must_be_positive(self) -> None:
        """HP must be at least 1."""
        with pytest.raises(ValidationError):
            _make_stat_block(hp=0)

    def test_attack_can_be_zero(self) -> None:
        """Attack and other non-HP stats can be 0."""
        stats = _make_stat_block(attack=0)
        assert stats.attack == 0

    def test_negative_stat_rejected(self) -> None:
        """Negative values should be rejected."""
        with pytest.raises(ValidationError):
            _make_stat_block(defense=-1)


# --- MonsterSpecies ---


class TestMonsterSpecies:
    """Tests for MonsterSpecies model."""

    def test_valid_construction(self) -> None:
        """MonsterSpecies should accept valid data."""
        species = _make_species()
        assert species.species_id == "sp_flame_wolf"
        assert species.name == "Flame Wolf"
        assert species.element == Element.FIRE
        assert species.rarity == Rarity.COMMON

    def test_empty_species_id_rejected(self) -> None:
        """species_id cannot be empty."""
        with pytest.raises(ValidationError):
            _make_species(species_id="")

    def test_defaults(self) -> None:
        """learnable_skill_ids should default to empty list."""
        species = _make_species()
        assert species.learnable_skill_ids == []

    def test_empty_name_rejected(self) -> None:
        """Name cannot be empty."""
        with pytest.raises(ValidationError):
            _make_species(name="")

    def test_long_name_rejected(self) -> None:
        """Name cannot exceed 50 characters."""
        with pytest.raises(ValidationError):
            _make_species(name="A" * 51)

    def test_learnable_skills(self) -> None:
        """learnable_skill_ids can hold skill IDs."""
        species = _make_species(learnable_skill_ids=["sk_1", "sk_2"])
        assert species.learnable_skill_ids == ["sk_1", "sk_2"]


# --- Monster ---


class TestMonster:
    """Tests for Monster model."""

    def test_valid_construction(self) -> None:
        """Monster should accept valid data."""
        mon = _make_monster()
        assert mon.monster_id == "mon_001"
        assert mon.level == 1
        assert mon.is_fainted is False

    def test_empty_monster_id_rejected(self) -> None:
        """monster_id cannot be empty."""
        with pytest.raises(ValidationError):
            _make_monster(monster_id="")

    def test_defaults(self) -> None:
        """Default values should be applied correctly."""
        mon = _make_monster()
        assert mon.level == 1
        assert mon.experience == 0
        assert mon.bond_level == 0
        assert mon.equipped_skill_ids == []
        assert mon.is_fainted is False

    def test_level_bounds(self) -> None:
        """Level must be between 1 and 100."""
        with pytest.raises(ValidationError):
            _make_monster(level=0)
        with pytest.raises(ValidationError):
            _make_monster(level=101)

    def test_bond_level_bounds(self) -> None:
        """Bond level must be between 0 and 100."""
        with pytest.raises(ValidationError):
            _make_monster(bond_level=-1)
        with pytest.raises(ValidationError):
            _make_monster(bond_level=101)

    def test_negative_experience_rejected(self) -> None:
        """Experience cannot be negative."""
        with pytest.raises(ValidationError):
            _make_monster(experience=-10)

    def test_negative_current_hp_rejected(self) -> None:
        """current_hp cannot be negative."""
        with pytest.raises(ValidationError):
            _make_monster(current_hp=-1)

    def test_max_equipped_skills(self) -> None:
        """Cannot equip more than 4 skills."""
        with pytest.raises(ValidationError):
            _make_monster(
                equipped_skill_ids=["s1", "s2", "s3", "s4", "s5"],
            )

    def test_effective_stats_level_1(self) -> None:
        """At level 1, effective stats equal base stats."""
        mon = _make_monster(level=1)
        effective = mon.effective_stats()
        base = mon.species.base_stats
        assert effective.hp == base.hp
        assert effective.attack == base.attack
        assert effective.defense == base.defense
        assert effective.speed == base.speed

    def test_effective_stats_level_50(self) -> None:
        """At level 50, stats should scale by 1 + 49*0.05 = 3.45."""
        mon = _make_monster(level=50)
        effective = mon.effective_stats()
        base = mon.species.base_stats
        expected_scale = 1.0 + 49 * 0.05  # 3.45
        assert effective.hp == round(base.hp * expected_scale)
        assert effective.attack == round(base.attack * expected_scale)

    def test_effective_stats_level_100(self) -> None:
        """At level 100, stats should scale by 1 + 99*0.05 = 5.95."""
        mon = _make_monster(level=100)
        effective = mon.effective_stats()
        base = mon.species.base_stats
        expected_scale = 1.0 + 99 * 0.05
        assert effective.hp == round(base.hp * expected_scale)
