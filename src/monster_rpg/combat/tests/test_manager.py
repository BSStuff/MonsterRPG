"""Tests for the combat manager."""

from monster_rpg.combat.manager import (
    CombatManager,
)
from monster_rpg.monsters.models import Element, Monster, MonsterSpecies, Rarity, StatBlock
from monster_rpg.skills.progression import Skill, SkillType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _species(
    species_id: str = "sp_fire",
    element: Element = Element.FIRE,
    hp: int = 100,
    attack: int = 50,
    defense: int = 40,
    speed: int = 30,
    magic_attack: int = 50,
    magic_defense: int = 40,
) -> MonsterSpecies:
    return MonsterSpecies(
        species_id=species_id,
        name=f"Mon_{species_id}",
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
        passive_trait="Trait",
        passive_description="Desc",
    )


def _monster(
    monster_id: str = "m1",
    element: Element = Element.FIRE,
    level: int = 10,
    current_hp: int = 100,
    speed: int = 30,
    equipped_skill_ids: list[str] | None = None,
    is_fainted: bool = False,
) -> Monster:
    return Monster(
        monster_id=monster_id,
        species=_species(element=element, speed=speed),
        level=level,
        current_hp=current_hp,
        equipped_skill_ids=equipped_skill_ids or ["sk_1"],
        is_fainted=is_fainted,
    )


def _skill(
    skill_id: str = "sk_1",
    name: str = "Slash",
    power: int = 60,
    element: Element = Element.NEUTRAL,
) -> Skill:
    return Skill(
        skill_id=skill_id,
        name=name,
        skill_type=SkillType.ATTACK,
        element=element,
        power=power,
        accuracy=100,
        cooldown=0.0,
        description="Test skill",
    )


def _registry(*skills: Skill) -> dict[str, Skill]:
    return {s.skill_id: s for s in skills}


# ---------------------------------------------------------------------------
# CombatManager initialization
# ---------------------------------------------------------------------------


class TestCombatManagerInit:
    """Tests for CombatManager initialization."""

    def test_initial_state(self) -> None:
        player = [_monster("p1")]
        enemy = [_monster("e1")]
        cm = CombatManager(player, enemy)
        assert cm.round_number == 0
        assert cm.is_finished is False
        assert cm.player_won is None
        assert cm.combat_log == []

    def test_teams_are_copies(self) -> None:
        """Modifying the original list should not affect the manager."""
        player = [_monster("p1")]
        enemy = [_monster("e1")]
        cm = CombatManager(player, enemy)
        player.append(_monster("p2"))
        assert len(cm.player_team) == 1


# ---------------------------------------------------------------------------
# get_active_monsters
# ---------------------------------------------------------------------------


class TestGetActiveMonsters:
    """Tests for filtering fainted monsters."""

    def test_all_active(self) -> None:
        team = [_monster("m1"), _monster("m2")]
        cm = CombatManager(team, [_monster("e1")])
        assert len(cm.get_active_monsters(cm.player_team)) == 2

    def test_filters_fainted(self) -> None:
        team = [_monster("m1"), _monster("m2", is_fainted=True)]
        cm = CombatManager(team, [_monster("e1")])
        active = cm.get_active_monsters(cm.player_team)
        assert len(active) == 1
        assert active[0].monster_id == "m1"

    def test_all_fainted_returns_empty(self) -> None:
        team = [
            _monster("m1", is_fainted=True),
            _monster("m2", is_fainted=True),
        ]
        cm = CombatManager(team, [_monster("e1")])
        assert cm.get_active_monsters(cm.player_team) == []


# ---------------------------------------------------------------------------
# get_turn_order
# ---------------------------------------------------------------------------


class TestGetTurnOrder:
    """Tests for speed-based turn ordering."""

    def test_sorted_by_speed_descending(self) -> None:
        fast = _monster("fast", speed=100)
        slow = _monster("slow", speed=10)
        cm = CombatManager([slow], [fast])
        order = cm.get_turn_order()
        assert order[0].monster_id == "fast"
        assert order[1].monster_id == "slow"

    def test_fainted_excluded(self) -> None:
        alive = _monster("alive", speed=50)
        dead = _monster("dead", speed=100, is_fainted=True)
        cm = CombatManager([alive], [dead])
        order = cm.get_turn_order()
        assert len(order) == 1
        assert order[0].monster_id == "alive"


# ---------------------------------------------------------------------------
# select_target
# ---------------------------------------------------------------------------


class TestSelectTarget:
    """Tests for target selection logic."""

    def test_picks_lowest_hp_enemy(self) -> None:
        player = _monster("p1")
        enemy_high = _monster("e_high", current_hp=100)
        enemy_low = _monster("e_low", current_hp=20)
        cm = CombatManager([player], [enemy_high, enemy_low])
        target = cm.select_target(player)
        assert target is not None
        assert target.monster_id == "e_low"

    def test_enemy_targets_player(self) -> None:
        player = _monster("p1", current_hp=30)
        enemy = _monster("e1")
        cm = CombatManager([player], [enemy])
        target = cm.select_target(enemy)
        assert target is not None
        assert target.monster_id == "p1"

    def test_no_targets_returns_none(self) -> None:
        player = _monster("p1")
        enemy = _monster("e1", is_fainted=True)
        cm = CombatManager([player], [enemy])
        assert cm.select_target(player) is None


# ---------------------------------------------------------------------------
# select_skill
# ---------------------------------------------------------------------------


class TestSelectSkill:
    """Tests for skill selection."""

    def test_picks_first_equipped_skill(self) -> None:
        mon = _monster("m1", equipped_skill_ids=["sk_a", "sk_b"])
        sk_a = _skill("sk_a", name="Alpha")
        sk_b = _skill("sk_b", name="Beta")
        cm = CombatManager([mon], [_monster("e1")])
        result = cm.select_skill(mon, _registry(sk_a, sk_b))
        assert result is not None
        assert result.skill_id == "sk_a"

    def test_no_skills_returns_none(self) -> None:
        mon = _monster("m1", equipped_skill_ids=[])
        cm = CombatManager([mon], [_monster("e1")])
        assert cm.select_skill(mon, {}) is None

    def test_missing_skill_in_registry(self) -> None:
        mon = _monster("m1", equipped_skill_ids=["missing"])
        cm = CombatManager([mon], [_monster("e1")])
        assert cm.select_skill(mon, {}) is None


# ---------------------------------------------------------------------------
# apply_damage
# ---------------------------------------------------------------------------


class TestApplyDamage:
    """Tests for damage application."""

    def test_reduces_hp(self) -> None:
        target = _monster("t", current_hp=50)
        cm = CombatManager([], [target])
        remaining, fainted = cm.apply_damage(target, 20)
        assert remaining == 30
        assert fainted is False
        assert target.current_hp == 30

    def test_faint_at_zero(self) -> None:
        target = _monster("t", current_hp=10)
        cm = CombatManager([], [target])
        remaining, fainted = cm.apply_damage(target, 10)
        assert remaining == 0
        assert fainted is True
        assert target.is_fainted is True

    def test_overkill_clamps_to_zero(self) -> None:
        target = _monster("t", current_hp=5)
        cm = CombatManager([], [target])
        remaining, fainted = cm.apply_damage(target, 100)
        assert remaining == 0
        assert fainted is True


# ---------------------------------------------------------------------------
# execute_round
# ---------------------------------------------------------------------------


class TestExecuteRound:
    """Tests for single round execution."""

    def test_produces_actions(self) -> None:
        player = _monster("p1", speed=50, current_hp=200)
        enemy = _monster("e1", speed=30, current_hp=200)
        skill = _skill("sk_1")
        cm = CombatManager([player], [enemy])
        result = cm.execute_round(_registry(skill))
        assert result.round_number == 1
        assert len(result.actions) >= 1

    def test_round_increments(self) -> None:
        player = _monster("p1", current_hp=500)
        enemy = _monster("e1", current_hp=500)
        skill = _skill("sk_1")
        cm = CombatManager([player], [enemy])
        cm.execute_round(_registry(skill))
        cm.execute_round(_registry(skill))
        assert cm.round_number == 2

    def test_no_op_after_finished(self) -> None:
        """Executing a round after combat ends should return empty result."""
        player = _monster("p1", speed=100, current_hp=500)
        enemy = _monster("e1", speed=10, current_hp=1)
        skill = _skill("sk_1", power=200)
        cm = CombatManager([player], [enemy])
        cm.execute_round(_registry(skill))
        assert cm.is_finished is True
        result = cm.execute_round(_registry(skill))
        assert result.actions == []


# ---------------------------------------------------------------------------
# run_combat — end-to-end
# ---------------------------------------------------------------------------


class TestRunCombat:
    """Tests for full combat runs."""

    def test_player_wins(self) -> None:
        """Strong player monster should defeat weak enemy."""
        player = _monster("p1", speed=100, current_hp=500, level=50)
        enemy = _monster("e1", speed=10, current_hp=50, level=1)
        skill = _skill("sk_1", power=100)
        cm = CombatManager([player], [enemy])
        results = cm.run_combat(_registry(skill))
        assert cm.is_finished is True
        assert cm.player_won is True
        assert len(results) >= 1

    def test_enemy_wins(self) -> None:
        """Strong enemy should defeat weak player."""
        player = _monster("p1", speed=10, current_hp=50, level=1)
        enemy = _monster("e1", speed=100, current_hp=500, level=50)
        skill = _skill("sk_1", power=100)
        cm = CombatManager([player], [enemy])
        cm.run_combat(_registry(skill))
        assert cm.is_finished is True
        assert cm.player_won is False

    def test_combat_log_populated(self) -> None:
        player = _monster("p1", speed=100, current_hp=500, level=50)
        enemy = _monster("e1", speed=10, current_hp=10, level=1)
        skill = _skill("sk_1", power=200)
        cm = CombatManager([player], [enemy])
        cm.run_combat(_registry(skill))
        assert len(cm.combat_log) >= 1

    def test_max_rounds_limit(self) -> None:
        """Combat should end after max_rounds even if no one faints."""
        # Both with very high HP and low power — won't finish naturally
        player = _monster("p1", speed=50, current_hp=99999, level=1)
        enemy = _monster("e1", speed=50, current_hp=99999, level=1)
        skill = _skill("sk_1", power=1)
        cm = CombatManager([player], [enemy])
        results = cm.run_combat(_registry(skill), max_rounds=3)
        assert len(results) == 3
        assert cm.round_number == 3

    def test_multi_monster_teams(self) -> None:
        """Combat with multiple monsters per side should resolve correctly."""
        p1 = _monster("p1", speed=90, current_hp=200, level=20)
        p2 = _monster("p2", speed=80, current_hp=200, level=20)
        e1 = _monster("e1", speed=70, current_hp=50, level=5)
        e2 = _monster("e2", speed=60, current_hp=50, level=5)
        skill = _skill("sk_1", power=100)
        cm = CombatManager([p1, p2], [e1, e2])
        cm.run_combat(_registry(skill))
        assert cm.is_finished is True
        assert cm.player_won is True

    def test_fainted_monster_ids_tracked(self) -> None:
        """Fainted monster IDs should appear in round results."""
        player = _monster("p1", speed=100, current_hp=500, level=50)
        enemy = _monster("e1", speed=10, current_hp=1, level=1)
        skill = _skill("sk_1", power=200)
        cm = CombatManager([player], [enemy])
        results = cm.run_combat(_registry(skill))
        all_fainted = []
        for r in results:
            all_fainted.extend(r.fainted_monster_ids)
        assert "e1" in all_fainted

    def test_single_vs_single_deterministic(self) -> None:
        """1v1 combat with deterministic factor should be reproducible."""

        def run_once() -> bool:
            p = _monster("p1", speed=50, current_hp=100, level=10)
            e = _monster("e1", speed=40, current_hp=100, level=10)
            skill = _skill("sk_1", power=60)
            cm = CombatManager([p], [e])
            cm.run_combat(_registry(skill), random_factor=1.0)
            return cm.player_won is True

        r1 = run_once()
        r2 = run_once()
        assert r1 == r2
