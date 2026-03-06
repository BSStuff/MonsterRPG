"""Tests for monster models."""

import pytest
from pydantic import ValidationError

from elements_rpg.config import MAX_MONSTER_LEVEL
from elements_rpg.monsters.models import (
    Element,
    Monster,
    MonsterSpecies,
    Rarity,
    StatBlock,
    xp_for_level,
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
        "types": (Element.FIRE, None),
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
        """All ten elements should be defined."""
        assert set(Element) == {
            Element.FIRE,
            Element.WATER,
            Element.GRASS,
            Element.ELECTRIC,
            Element.WIND,
            Element.GROUND,
            Element.ROCK,
            Element.DARK,
            Element.LIGHT,
            Element.ICE,
        }

    def test_element_values(self) -> None:
        """Element values should be lowercase strings."""
        assert Element.FIRE.value == "fire"
        assert Element.DARK.value == "dark"


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


# --- xp_for_level function ---


class TestXpForLevel:
    """Tests for the xp_for_level helper function."""

    def test_level_1_requires_zero_xp(self) -> None:
        """Level 1 is the starting level and requires 0 XP."""
        assert xp_for_level(1) == 0

    def test_level_2(self) -> None:
        """Level 2 should require ~282 XP (100 * 2^1.5)."""
        assert xp_for_level(2) == int(100 * (2**1.5))

    def test_level_5(self) -> None:
        """Level 5 XP follows the formula."""
        assert xp_for_level(5) == int(100 * (5**1.5))

    def test_level_10(self) -> None:
        """Level 10 XP follows the formula."""
        assert xp_for_level(10) == int(100 * (10**1.5))

    def test_level_50(self) -> None:
        """Level 50 XP follows the formula."""
        assert xp_for_level(50) == int(100 * (50**1.5))

    def test_level_100(self) -> None:
        """Level 100 XP follows the formula."""
        assert xp_for_level(100) == int(100 * (100**1.5))

    def test_monotonically_increasing(self) -> None:
        """XP requirements should increase with each level."""
        for lvl in range(2, 100):
            assert xp_for_level(lvl + 1) > xp_for_level(lvl)

    def test_invalid_level_zero(self) -> None:
        """Level 0 should raise ValueError."""
        with pytest.raises(ValueError, match="Level must be >= 1"):
            xp_for_level(0)


# --- Monster XP / Leveling ---


class TestMonsterExperience:
    """Tests for Monster.gain_experience and leveling."""

    def test_gain_xp_single_level(self) -> None:
        """Gaining enough XP for exactly one level-up."""
        mon = _make_monster()
        xp_needed = xp_for_level(2)
        levels = mon.gain_experience(xp_needed)
        assert levels == [2]
        assert mon.level == 2
        assert mon.experience == 0

    def test_gain_xp_multiple_levels(self) -> None:
        """Gaining enough XP for multiple level-ups at once."""
        mon = _make_monster()
        # Give enough XP for levels 2 and 3
        total_xp = xp_for_level(2) + xp_for_level(3) + 10
        levels = mon.gain_experience(total_xp)
        assert levels == [2, 3]
        assert mon.level == 3
        assert mon.experience == 10  # leftover

    def test_gain_xp_caps_at_max_level(self) -> None:
        """XP gain should stop at MAX_MONSTER_LEVEL."""
        mon = _make_monster(level=99)
        xp_needed = xp_for_level(100)
        levels = mon.gain_experience(xp_needed + 9999)
        assert 100 in levels
        assert mon.level == MAX_MONSTER_LEVEL
        assert mon.experience == 0  # excess XP discarded at max

    def test_gain_xp_at_max_level_returns_empty(self) -> None:
        """A max-level monster should gain no levels."""
        mon = _make_monster(level=MAX_MONSTER_LEVEL)
        levels = mon.gain_experience(99999)
        assert levels == []
        assert mon.level == MAX_MONSTER_LEVEL

    def test_leftover_xp_retained(self) -> None:
        """Leftover XP after a level-up should be kept."""
        mon = _make_monster()
        xp_needed = xp_for_level(2)
        leftover = 42
        levels = mon.gain_experience(xp_needed + leftover)
        assert levels == [2]
        assert mon.experience == leftover

    def test_gain_zero_xp(self) -> None:
        """Gaining 0 XP should be a no-op."""
        mon = _make_monster()
        levels = mon.gain_experience(0)
        assert levels == []
        assert mon.level == 1

    def test_gain_negative_xp_raises(self) -> None:
        """Negative XP should raise ValueError."""
        mon = _make_monster()
        with pytest.raises(ValueError, match="non-negative"):
            mon.gain_experience(-1)

    def test_current_hp_unchanged_on_levelup(self) -> None:
        """Level-up should NOT modify current_hp."""
        mon = _make_monster(current_hp=50)
        xp_needed = xp_for_level(2)
        mon.gain_experience(xp_needed)
        assert mon.current_hp == 50


# --- Monster Bond ---


class TestMonsterBond:
    """Tests for Monster.gain_bond and bond effects."""

    def test_gain_bond_increases(self) -> None:
        """gain_bond should increase bond_level."""
        mon = _make_monster()
        result = mon.gain_bond(10)
        assert result == 10
        assert mon.bond_level == 10

    def test_gain_bond_caps_at_100(self) -> None:
        """Bond level should not exceed 100."""
        mon = _make_monster(bond_level=95)
        result = mon.gain_bond(20)
        assert result == 100
        assert mon.bond_level == 100

    def test_gain_bond_already_at_max(self) -> None:
        """Gaining bond at max should stay at 100."""
        mon = _make_monster(bond_level=100)
        result = mon.gain_bond(10)
        assert result == 100

    def test_bond_affects_effective_stats(self) -> None:
        """Stats at bond 100 should be ~20% higher than at bond 0."""
        mon_no_bond = _make_monster(bond_level=0)
        mon_max_bond = _make_monster(bond_level=100)
        stats_0 = mon_no_bond.effective_stats()
        stats_100 = mon_max_bond.effective_stats()
        # Bond 100 = 1.0 + 100*0.002 = 1.20 multiplier
        assert stats_100.hp > stats_0.hp
        assert stats_100.attack > stats_0.attack
        assert stats_100.hp == round(stats_0.hp * 1.2)
        assert stats_100.attack == round(stats_0.attack * 1.2)

    def test_bond_multiplier_at_50(self) -> None:
        """Bond 50 should give a ~10% bonus (multiplier 1.10)."""
        mon = _make_monster(bond_level=50)
        base = mon.species.base_stats
        effective = mon.effective_stats()
        # Level 1 scale = 1.0, bond 50 = 1.0 + 50*0.002 = 1.10
        assert effective.hp == round(base.hp * 1.10)
        assert effective.attack == round(base.attack * 1.10)

    def test_gain_bond_negative_raises(self) -> None:
        """Negative bond amount should raise ValueError."""
        mon = _make_monster()
        with pytest.raises(ValueError, match="non-negative"):
            mon.gain_bond(-5)


# --- Monster Skill Management ---


class TestMonsterSkillManagement:
    """Tests for equip_skill, unequip_skill, can_learn_skill."""

    def _make_monster_with_skills(self) -> Monster:
        """Create a monster whose species can learn 5 skills."""
        species = _make_species(
            learnable_skill_ids=["sk_1", "sk_2", "sk_3", "sk_4", "sk_5"],
        )
        return _make_monster(species=species)

    def test_can_learn_skill_true(self) -> None:
        """can_learn_skill returns True for a learnable skill."""
        mon = self._make_monster_with_skills()
        assert mon.can_learn_skill("sk_1") is True

    def test_can_learn_skill_false(self) -> None:
        """can_learn_skill returns False for a non-learnable skill."""
        mon = self._make_monster_with_skills()
        assert mon.can_learn_skill("sk_unknown") is False

    def test_equip_skill_success(self) -> None:
        """equip_skill should succeed for a learnable skill with open slots."""
        mon = self._make_monster_with_skills()
        assert mon.equip_skill("sk_1") is True
        assert "sk_1" in mon.equipped_skill_ids

    def test_equip_skill_fails_at_max_slots(self) -> None:
        """equip_skill should fail when all 4 slots are occupied."""
        mon = self._make_monster_with_skills()
        mon.equip_skill("sk_1")
        mon.equip_skill("sk_2")
        mon.equip_skill("sk_3")
        mon.equip_skill("sk_4")
        assert mon.equip_skill("sk_5") is False
        assert len(mon.equipped_skill_ids) == 4

    def test_equip_skill_fails_for_non_learnable(self) -> None:
        """equip_skill should fail for a skill not in learnable_skill_ids."""
        mon = self._make_monster_with_skills()
        assert mon.equip_skill("sk_unknown") is False
        assert mon.equipped_skill_ids == []

    def test_equip_skill_fails_for_duplicate(self) -> None:
        """equip_skill should reject equipping the same skill twice."""
        mon = self._make_monster_with_skills()
        mon.equip_skill("sk_1")
        assert mon.equip_skill("sk_1") is False
        assert mon.equipped_skill_ids.count("sk_1") == 1

    def test_unequip_skill_success(self) -> None:
        """unequip_skill should remove an equipped skill."""
        mon = self._make_monster_with_skills()
        mon.equip_skill("sk_1")
        assert mon.unequip_skill("sk_1") is True
        assert "sk_1" not in mon.equipped_skill_ids

    def test_unequip_skill_not_equipped(self) -> None:
        """unequip_skill should return False for a non-equipped skill."""
        mon = self._make_monster_with_skills()
        assert mon.unequip_skill("sk_1") is False

    def test_equip_after_unequip(self) -> None:
        """Should be able to equip a new skill after unequipping one."""
        mon = self._make_monster_with_skills()
        mon.equip_skill("sk_1")
        mon.equip_skill("sk_2")
        mon.equip_skill("sk_3")
        mon.equip_skill("sk_4")
        mon.unequip_skill("sk_2")
        assert mon.equip_skill("sk_5") is True
        assert "sk_5" in mon.equipped_skill_ids
        assert len(mon.equipped_skill_ids) == 4


# --- Monster max_hp ---


class TestMonsterMaxHp:
    """Tests for Monster.max_hp."""

    def test_max_hp_matches_effective_stats(self) -> None:
        """max_hp should return the same value as effective_stats().hp."""
        mon = _make_monster(level=10, bond_level=25)
        assert mon.max_hp() == mon.effective_stats().hp

    def test_max_hp_at_level_1_bond_0(self) -> None:
        """At level 1 bond 0, max_hp should equal base hp."""
        mon = _make_monster()
        assert mon.max_hp() == mon.species.base_stats.hp
