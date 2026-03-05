"""Tests for damage calculation logic."""

from elements_rpg.combat.damage_calc import (
    ELEMENT_CHART,
    calculate_damage,
    get_element_multiplier,
)
from elements_rpg.monsters.models import Element, Monster, MonsterSpecies, Rarity, StatBlock
from elements_rpg.skills.progression import Skill, SkillType

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_species(
    element: Element = Element.FIRE,
    attack: int = 50,
    defense: int = 40,
    magic_attack: int = 50,
    magic_defense: int = 40,
    speed: int = 30,
    hp: int = 100,
) -> MonsterSpecies:
    """Create a test monster species with configurable stats."""
    return MonsterSpecies(
        species_id="test_species",
        name="TestMon",
        element=element,
        rarity=Rarity.COMMON,
        base_stats=StatBlock(
            hp=hp,
            attack=attack,
            defense=defense,
            speed=speed,
            magic_attack=magic_attack,
            magic_defense=magic_defense,
        ),
        passive_trait="Test Trait",
        passive_description="Does nothing.",
    )


def _make_monster(
    monster_id: str = "mon_1",
    element: Element = Element.FIRE,
    level: int = 10,
    current_hp: int = 100,
    attack: int = 50,
    defense: int = 40,
    magic_attack: int = 50,
    magic_defense: int = 40,
) -> Monster:
    """Create a test monster with configurable parameters."""
    species = _make_species(
        element=element,
        attack=attack,
        defense=defense,
        magic_attack=magic_attack,
        magic_defense=magic_defense,
    )
    return Monster(
        monster_id=monster_id,
        species=species,
        level=level,
        current_hp=current_hp,
        equipped_skill_ids=[],
    )


def _make_skill(
    skill_id: str = "sk_1",
    name: str = "Fireball",
    skill_type: SkillType = SkillType.ATTACK,
    element: Element = Element.FIRE,
    power: int = 60,
    level: int = 1,
) -> Skill:
    """Create a test skill with configurable parameters."""
    return Skill(
        skill_id=skill_id,
        name=name,
        skill_type=skill_type,
        element=element,
        power=power,
        accuracy=100,
        cooldown=0.0,
        description="A test skill.",
        level=level,
    )


# ---------------------------------------------------------------------------
# get_element_multiplier tests
# ---------------------------------------------------------------------------


class TestGetElementMultiplier:
    """Tests for the element effectiveness lookup."""

    def test_super_effective_fire_vs_wind(self) -> None:
        assert get_element_multiplier(Element.FIRE, Element.WIND) == 1.5

    def test_super_effective_water_vs_fire(self) -> None:
        assert get_element_multiplier(Element.WATER, Element.FIRE) == 1.5

    def test_super_effective_earth_vs_water(self) -> None:
        assert get_element_multiplier(Element.EARTH, Element.WATER) == 1.5

    def test_super_effective_wind_vs_earth(self) -> None:
        assert get_element_multiplier(Element.WIND, Element.EARTH) == 1.5

    def test_not_effective_fire_vs_water(self) -> None:
        assert get_element_multiplier(Element.FIRE, Element.WATER) == 0.5

    def test_not_effective_water_vs_earth(self) -> None:
        assert get_element_multiplier(Element.WATER, Element.EARTH) == 0.5

    def test_not_effective_earth_vs_wind(self) -> None:
        assert get_element_multiplier(Element.EARTH, Element.WIND) == 0.5

    def test_not_effective_wind_vs_fire(self) -> None:
        assert get_element_multiplier(Element.WIND, Element.FIRE) == 0.5

    def test_neutral_same_element(self) -> None:
        assert get_element_multiplier(Element.FIRE, Element.FIRE) == 1.0

    def test_neutral_element_vs_neutral(self) -> None:
        assert get_element_multiplier(Element.FIRE, Element.NEUTRAL) == 1.0

    def test_neutral_attacking_with_neutral(self) -> None:
        assert get_element_multiplier(Element.NEUTRAL, Element.FIRE) == 1.0

    def test_all_chart_entries_have_valid_elements(self) -> None:
        """Verify all entries in ELEMENT_CHART use valid Element values."""
        for (atk, dfn), mult in ELEMENT_CHART.items():
            assert isinstance(atk, Element)
            assert isinstance(dfn, Element)
            assert mult in (0.5, 1.5)


# ---------------------------------------------------------------------------
# calculate_damage tests
# ---------------------------------------------------------------------------


class TestCalculateDamage:
    """Tests for the main damage calculation function."""

    def test_basic_damage_positive(self) -> None:
        """Damage should be a positive integer."""
        attacker = _make_monster(element=Element.FIRE, level=10)
        defender = _make_monster(monster_id="mon_2", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.FIRE, power=60)
        damage = calculate_damage(attacker, defender, skill)
        assert damage >= 1
        assert isinstance(damage, int)

    def test_deterministic_with_default_random_factor(self) -> None:
        """Same inputs should produce same output with default random_factor."""
        attacker = _make_monster(element=Element.FIRE, level=10)
        defender = _make_monster(monster_id="mon_2", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.FIRE, power=60)
        d1 = calculate_damage(attacker, defender, skill)
        d2 = calculate_damage(attacker, defender, skill)
        assert d1 == d2

    def test_super_effective_more_damage(self) -> None:
        """Super effective hits should deal more damage than neutral."""
        attacker = _make_monster(element=Element.FIRE, level=10)
        defender_weak = _make_monster(monster_id="mon_w", element=Element.WIND, level=10)
        defender_neutral = _make_monster(monster_id="mon_n", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.FIRE, power=60)
        dmg_se = calculate_damage(attacker, defender_weak, skill)
        dmg_neutral = calculate_damage(attacker, defender_neutral, skill)
        assert dmg_se > dmg_neutral

    def test_not_effective_less_damage(self) -> None:
        """Not very effective hits should deal less damage than neutral."""
        attacker = _make_monster(element=Element.FIRE, level=10)
        defender_resist = _make_monster(monster_id="mon_r", element=Element.WATER, level=10)
        defender_neutral = _make_monster(monster_id="mon_n", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.FIRE, power=60)
        dmg_nve = calculate_damage(attacker, defender_resist, skill)
        dmg_neutral = calculate_damage(attacker, defender_neutral, skill)
        assert dmg_nve < dmg_neutral

    def test_stab_bonus(self) -> None:
        """STAB should increase damage when skill element matches monster element."""
        attacker_stab = _make_monster(element=Element.FIRE, level=10)
        attacker_no_stab = _make_monster(monster_id="mon_ns", element=Element.WATER, level=10)
        defender = _make_monster(monster_id="mon_d", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.FIRE, power=60)
        dmg_stab = calculate_damage(attacker_stab, defender, skill)
        dmg_no_stab = calculate_damage(attacker_no_stab, defender, skill)
        assert dmg_stab > dmg_no_stab

    def test_skill_level_bonus(self) -> None:
        """Higher skill level should deal more damage."""
        attacker = _make_monster(element=Element.NEUTRAL, level=10)
        defender = _make_monster(monster_id="mon_d", element=Element.NEUTRAL, level=10)
        skill_lv1 = _make_skill(element=Element.NEUTRAL, power=80, level=1)
        skill_lv10 = _make_skill(element=Element.NEUTRAL, power=80, level=10)
        dmg_lv1 = calculate_damage(attacker, defender, skill_lv1)
        dmg_lv10 = calculate_damage(attacker, defender, skill_lv10)
        assert dmg_lv10 > dmg_lv1

    def test_minimum_damage_is_one(self) -> None:
        """Damage should never drop below 1."""
        attacker = _make_monster(element=Element.FIRE, level=1, attack=1)
        defender = _make_monster(monster_id="mon_d", element=Element.WATER, level=100, defense=999)
        skill = _make_skill(element=Element.FIRE, power=1, level=1)
        damage = calculate_damage(attacker, defender, skill, random_factor=0.85)
        assert damage >= 1

    def test_zero_defense_no_crash(self) -> None:
        """Zero defense should not cause division by zero."""
        attacker = _make_monster(element=Element.FIRE, level=10)
        defender = _make_monster(monster_id="mon_d", element=Element.NEUTRAL, defense=0)
        skill = _make_skill(element=Element.FIRE, power=60)
        damage = calculate_damage(attacker, defender, skill)
        assert damage >= 1

    def test_special_skill_uses_magic_stats(self) -> None:
        """Non-ATTACK skill types should use magic_attack and magic_defense."""
        attacker = _make_monster(element=Element.FIRE, level=10, attack=10, magic_attack=100)
        defender = _make_monster(
            monster_id="mon_d",
            element=Element.NEUTRAL,
            defense=100,
            magic_defense=10,
        )
        physical_skill = _make_skill(skill_type=SkillType.ATTACK, element=Element.NEUTRAL, power=60)
        special_skill = _make_skill(skill_type=SkillType.SPECIAL, element=Element.NEUTRAL, power=60)
        dmg_phys = calculate_damage(attacker, defender, physical_skill)
        dmg_spec = calculate_damage(attacker, defender, special_skill)
        # With 100 magic_attack vs 10 magic_defense, special should do more
        assert dmg_spec > dmg_phys

    def test_random_factor_reduces_damage(self) -> None:
        """A random factor < 1.0 should reduce damage."""
        attacker = _make_monster(element=Element.FIRE, level=10)
        defender = _make_monster(monster_id="mon_d", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.NEUTRAL, power=100)
        dmg_full = calculate_damage(attacker, defender, skill, random_factor=1.0)
        dmg_reduced = calculate_damage(attacker, defender, skill, random_factor=0.85)
        assert dmg_reduced <= dmg_full

    def test_higher_level_more_damage(self) -> None:
        """Higher level attacker should deal more damage."""
        attacker_low = _make_monster(element=Element.NEUTRAL, level=5)
        attacker_high = _make_monster(monster_id="mon_h", element=Element.NEUTRAL, level=50)
        defender = _make_monster(monster_id="mon_d", element=Element.NEUTRAL, level=10)
        skill = _make_skill(element=Element.NEUTRAL, power=60)
        dmg_low = calculate_damage(attacker_low, defender, skill)
        dmg_high = calculate_damage(attacker_high, defender, skill)
        assert dmg_high > dmg_low
