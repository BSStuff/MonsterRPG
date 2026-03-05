"""Combat manager — auto-combat loop with turn-based resolution."""

from dataclasses import dataclass, field

from elements_rpg.combat.damage_calc import calculate_damage
from elements_rpg.monsters.models import Monster
from elements_rpg.skills.progression import Skill


@dataclass
class CombatAction:
    """A single combat action to be resolved."""

    attacker: Monster
    defender: Monster
    skill: Skill


@dataclass
class CombatResult:
    """Result of a single combat action."""

    attacker_id: str
    defender_id: str
    skill_name: str
    damage_dealt: int
    defender_remaining_hp: int
    defender_fainted: bool


@dataclass
class CombatRoundResult:
    """Result of a full combat round."""

    round_number: int
    actions: list[CombatResult] = field(default_factory=list)
    fainted_monster_ids: list[str] = field(default_factory=list)


class CombatManager:
    """Manages auto-combat encounters between two teams of monsters.

    Turn resolution: Monsters act in speed order (highest first).
    Each monster uses one skill per round.
    Combat ends when all monsters on one side are fainted.
    """

    def __init__(
        self,
        player_team: list[Monster],
        enemy_team: list[Monster],
    ) -> None:
        self.player_team = list(player_team)
        self.enemy_team = list(enemy_team)
        self.round_number = 0
        self.combat_log: list[CombatRoundResult] = []
        self._is_finished = False
        self._player_won: bool | None = None

    @property
    def is_finished(self) -> bool:
        """Whether the combat has ended."""
        return self._is_finished

    @property
    def player_won(self) -> bool | None:
        """Whether the player won. None if combat is not finished."""
        return self._player_won

    def get_active_monsters(self, team: list[Monster]) -> list[Monster]:
        """Get non-fainted monsters from a team.

        Args:
            team: List of monsters to filter.

        Returns:
            List of monsters that have not fainted.
        """
        return [m for m in team if not m.is_fainted]

    def get_turn_order(self) -> list[Monster]:
        """Get all active monsters sorted by speed (descending).

        Returns:
            List of active monsters ordered by effective speed, fastest first.
        """
        all_active = self.get_active_monsters(self.player_team) + self.get_active_monsters(
            self.enemy_team
        )
        return sorted(
            all_active,
            key=lambda m: m.effective_stats().speed,
            reverse=True,
        )

    def select_target(self, attacker: Monster) -> Monster | None:
        """Select a target for the attacker based on strategy.

        Default targeting: lowest HP enemy. Can be expanded with strategy AI.

        Args:
            attacker: The monster selecting a target.

        Returns:
            The selected target monster, or None if no targets available.
        """
        if attacker in self.player_team:
            enemies = self.get_active_monsters(self.enemy_team)
        else:
            enemies = self.get_active_monsters(self.player_team)

        if not enemies:
            return None

        return min(enemies, key=lambda m: m.current_hp)

    def select_skill(self, monster: Monster, available_skills: dict[str, Skill]) -> Skill | None:
        """Select a skill for the monster to use.

        Uses the first available equipped skill.

        Args:
            monster: The monster selecting a skill.
            available_skills: Registry of skill_id to Skill objects.

        Returns:
            The selected skill, or None if no skills available.
        """
        for skill_id in monster.equipped_skill_ids:
            if skill_id in available_skills:
                return available_skills[skill_id]
        return None

    def apply_damage(self, target: Monster, damage: int) -> tuple[int, bool]:
        """Apply damage to a target monster.

        Args:
            target: The monster receiving damage.
            damage: The amount of damage to apply.

        Returns:
            Tuple of (remaining_hp, did_faint).
        """
        new_hp = max(target.current_hp - damage, 0)
        fainted = new_hp == 0
        target.current_hp = new_hp
        if fainted:
            target.is_fainted = True
        return new_hp, fainted

    def execute_round(
        self,
        skill_registry: dict[str, Skill],
        random_factor: float = 1.0,
    ) -> CombatRoundResult:
        """Execute one round of combat.

        Each active monster acts once in speed order. Combat ends when all
        monsters on one side have fainted.

        Args:
            skill_registry: Mapping of skill_id to Skill objects.
            random_factor: Random variance for damage (1.0 = deterministic).

        Returns:
            The result of this combat round.
        """
        if self._is_finished:
            return CombatRoundResult(round_number=self.round_number)

        self.round_number += 1
        round_result = CombatRoundResult(round_number=self.round_number)

        turn_order = self.get_turn_order()

        for monster in turn_order:
            # Skip if fainted during this round
            if monster.is_fainted:
                continue

            target = self.select_target(monster)
            if target is None:
                continue

            skill = self.select_skill(monster, skill_registry)
            if skill is None:
                continue

            damage = calculate_damage(
                attacker=monster,
                defender=target,
                skill=skill,
                random_factor=random_factor,
            )

            remaining_hp, fainted = self.apply_damage(target, damage)

            action_result = CombatResult(
                attacker_id=monster.monster_id,
                defender_id=target.monster_id,
                skill_name=skill.name,
                damage_dealt=damage,
                defender_remaining_hp=remaining_hp,
                defender_fainted=fainted,
            )
            round_result.actions.append(action_result)

            if fainted:
                round_result.fainted_monster_ids.append(target.monster_id)

            # Check if combat is over
            if not self.get_active_monsters(self.enemy_team):
                self._is_finished = True
                self._player_won = True
                break
            if not self.get_active_monsters(self.player_team):
                self._is_finished = True
                self._player_won = False
                break

        self.combat_log.append(round_result)
        return round_result

    def run_combat(
        self,
        skill_registry: dict[str, Skill],
        max_rounds: int = 100,
        random_factor: float = 1.0,
    ) -> list[CombatRoundResult]:
        """Run combat to completion or max rounds.

        Args:
            skill_registry: Mapping of skill_id to Skill objects.
            max_rounds: Maximum number of rounds before forced end.
            random_factor: Random variance for damage (1.0 = deterministic).

        Returns:
            List of all round results.
        """
        results: list[CombatRoundResult] = []
        while not self._is_finished and self.round_number < max_rounds:
            result = self.execute_round(skill_registry, random_factor)
            results.append(result)
        return results
