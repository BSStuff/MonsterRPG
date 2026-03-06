"""Tests for the strategy AI behavior system and target selection."""

from elements_rpg.combat.strategy import StrategyType
from elements_rpg.monsters.models import Element, Monster, MonsterSpecies, Rarity, StatBlock
from elements_rpg.skills.strategy_ai import (
    STRATEGY_BEHAVIORS,
    StrategyBehavior,
    get_strategy_behavior,
    select_target_by_strategy,
)


def _make_species(**overrides: object) -> MonsterSpecies:
    """Create a MonsterSpecies with sensible defaults."""
    defaults: dict[str, object] = {
        "species_id": "sp_test",
        "name": "TestMon",
        "types": (Element.DARK, None),
        "rarity": Rarity.COMMON,
        "base_stats": StatBlock(
            hp=100, attack=20, defense=15, speed=10, magic_attack=10, magic_defense=10
        ),
        "passive_trait": "Test Trait",
        "passive_description": "Does nothing",
    }
    defaults.update(overrides)
    return MonsterSpecies(**defaults)


def _make_monster(
    monster_id: str = "mon_1",
    current_hp: int = 100,
    attack: int = 20,
    base_hp: int = 100,
    **overrides: object,
) -> Monster:
    """Create a Monster with sensible defaults.

    Args:
        monster_id: Unique ID for the monster.
        current_hp: Current HP in combat (can be 0 for fainted).
        attack: Base attack stat.
        base_hp: Base HP stat for the species (must be >= 1).
    """
    species = _make_species(
        base_stats=StatBlock(
            hp=base_hp,
            attack=attack,
            defense=15,
            speed=10,
            magic_attack=10,
            magic_defense=10,
        ),
    )
    defaults: dict[str, object] = {
        "monster_id": monster_id,
        "species": species,
        "current_hp": current_hp,
    }
    defaults.update(overrides)
    return Monster(**defaults)


class TestStrategyBehavior:
    """Tests for StrategyBehavior dataclass."""

    def test_dataclass_fields(self) -> None:
        """StrategyBehavior should have all expected fields."""
        behavior = StrategyBehavior(
            strategy=StrategyType.AGGRESSIVE,
            description="Test",
            chase_range=10.0,
            heal_priority=False,
            follow_player=False,
            aggression=1.0,
        )
        assert behavior.strategy == StrategyType.AGGRESSIVE
        assert behavior.description == "Test"
        assert behavior.chase_range == 10.0
        assert behavior.heal_priority is False
        assert behavior.follow_player is False
        assert behavior.aggression == 1.0


class TestStrategyBehaviors:
    """Tests for STRATEGY_BEHAVIORS dictionary."""

    def test_all_five_strategies_defined(self) -> None:
        """All 5 PRD strategies should have behavior definitions."""
        assert set(STRATEGY_BEHAVIORS.keys()) == set(StrategyType)

    def test_attack_nearest_behavior(self) -> None:
        """ATTACK_NEAREST has moderate chase range and aggression."""
        b = STRATEGY_BEHAVIORS[StrategyType.ATTACK_NEAREST]
        assert b.chase_range == 5.0
        assert b.heal_priority is False
        assert b.follow_player is False
        assert b.aggression == 0.7

    def test_follow_player_behavior(self) -> None:
        """FOLLOW_PLAYER should follow player."""
        b = STRATEGY_BEHAVIORS[StrategyType.FOLLOW_PLAYER]
        assert b.follow_player is True
        assert b.aggression == 0.5

    def test_defensive_no_chase(self) -> None:
        """DEFENSIVE should have 0 chase range."""
        b = STRATEGY_BEHAVIORS[StrategyType.DEFENSIVE]
        assert b.chase_range == 0.0
        assert b.aggression == 0.3

    def test_aggressive_long_chase(self) -> None:
        """AGGRESSIVE should have longest chase range and max aggression."""
        b = STRATEGY_BEHAVIORS[StrategyType.AGGRESSIVE]
        assert b.chase_range == 15.0
        assert b.aggression == 1.0

    def test_heal_lowest_heal_priority(self) -> None:
        """HEAL_LOWEST should prioritize healing."""
        b = STRATEGY_BEHAVIORS[StrategyType.HEAL_LOWEST]
        assert b.heal_priority is True
        assert b.follow_player is True
        assert b.aggression == 0.2


class TestGetStrategyBehavior:
    """Tests for get_strategy_behavior function."""

    def test_returns_correct_behavior(self) -> None:
        """Should return the matching StrategyBehavior."""
        behavior = get_strategy_behavior(StrategyType.AGGRESSIVE)
        assert behavior.strategy == StrategyType.AGGRESSIVE

    def test_all_strategies_retrievable(self) -> None:
        """Every strategy type should be retrievable."""
        for strategy in StrategyType:
            behavior = get_strategy_behavior(strategy)
            assert behavior.strategy == strategy


class TestSelectTargetByStrategy:
    """Tests for select_target_by_strategy function."""

    def test_attack_nearest_returns_first_enemy(self) -> None:
        """ATTACK_NEAREST should return the first active enemy."""
        attacker = _make_monster("attacker")
        enemies = [_make_monster("e1"), _make_monster("e2")]
        result = select_target_by_strategy(StrategyType.ATTACK_NEAREST, attacker, [], enemies)
        assert result is not None
        assert result.monster_id == "e1"

    def test_aggressive_targets_lowest_hp(self) -> None:
        """AGGRESSIVE should target the enemy with lowest current HP."""
        attacker = _make_monster("attacker")
        enemies = [
            _make_monster("e1", current_hp=50),
            _make_monster("e2", current_hp=10),
            _make_monster("e3", current_hp=80),
        ]
        result = select_target_by_strategy(StrategyType.AGGRESSIVE, attacker, [], enemies)
        assert result is not None
        assert result.monster_id == "e2"

    def test_defensive_targets_highest_attack(self) -> None:
        """DEFENSIVE should target enemy with highest attack stat."""
        attacker = _make_monster("attacker")
        enemies = [
            _make_monster("e1", attack=10),
            _make_monster("e2", attack=50),
            _make_monster("e3", attack=30),
        ]
        result = select_target_by_strategy(StrategyType.DEFENSIVE, attacker, [], enemies)
        assert result is not None
        assert result.monster_id == "e2"

    def test_heal_lowest_targets_lowest_hp_ally(self) -> None:
        """HEAL_LOWEST should target ally with lowest HP percentage."""
        attacker = _make_monster("attacker")
        # a1: 100/100 = 100%, a2: 10/100 = 10% — a2 should be chosen
        ally_full = _make_monster("a1", current_hp=100, base_hp=100)
        ally_hurt = _make_monster("a2", current_hp=10, base_hp=100)
        allies = [ally_full, ally_hurt]
        result = select_target_by_strategy(StrategyType.HEAL_LOWEST, attacker, allies, [])
        assert result is not None
        assert result.monster_id == "a2"

    def test_heal_lowest_no_allies_no_enemies_returns_none(self) -> None:
        """HEAL_LOWEST with no allies and no enemies returns None."""
        attacker = _make_monster("attacker")
        result = select_target_by_strategy(StrategyType.HEAL_LOWEST, attacker, [], [])
        assert result is None

    def test_follow_player_returns_first_enemy(self) -> None:
        """FOLLOW_PLAYER should target first enemy (same as nearest)."""
        attacker = _make_monster("attacker")
        enemies = [_make_monster("e1"), _make_monster("e2")]
        result = select_target_by_strategy(StrategyType.FOLLOW_PLAYER, attacker, [], enemies)
        assert result is not None
        assert result.monster_id == "e1"

    def test_no_enemies_returns_none(self) -> None:
        """With no enemies, non-heal strategies return None."""
        attacker = _make_monster("attacker")
        result = select_target_by_strategy(StrategyType.ATTACK_NEAREST, attacker, [], [])
        assert result is None

    def test_all_fainted_enemies_returns_none(self) -> None:
        """Fainted enemies should be excluded; returns None if all fainted."""
        attacker = _make_monster("attacker")
        fainted = _make_monster("e1", current_hp=0, base_hp=50)
        fainted.is_fainted = True
        result = select_target_by_strategy(StrategyType.ATTACK_NEAREST, attacker, [], [fainted])
        assert result is None

    def test_fainted_allies_excluded_from_heal(self) -> None:
        """Fainted allies should not be heal targets."""
        attacker = _make_monster("attacker")
        fainted_ally = _make_monster("a1", current_hp=0, base_hp=50)
        fainted_ally.is_fainted = True
        healthy_ally = _make_monster("a2", current_hp=50)
        result = select_target_by_strategy(
            StrategyType.HEAL_LOWEST, attacker, [fainted_ally, healthy_ally], []
        )
        assert result is not None
        assert result.monster_id == "a2"

    def test_attacker_excluded_from_heal_targets(self) -> None:
        """The attacker itself should not be a heal target."""
        attacker = _make_monster("attacker", current_hp=1)
        ally = _make_monster("ally", current_hp=50)
        result = select_target_by_strategy(StrategyType.HEAL_LOWEST, attacker, [attacker, ally], [])
        assert result is not None
        assert result.monster_id == "ally"
