"""Strategy AI behavior definitions and target selection logic."""

from dataclasses import dataclass

from elements_rpg.combat.strategy import StrategyType
from elements_rpg.monsters.models import Monster


@dataclass
class StrategyBehavior:
    """Defines how a strategy modifies combat behavior.

    Attributes:
        strategy: The strategy type this behavior belongs to.
        description: Human-readable description of the strategy.
        chase_range: How far monster will chase enemies (0 = no chase).
        heal_priority: Whether to prioritize healing allies.
        follow_player: Whether to stay near the player.
        aggression: Aggression level from 0.0 (passive) to 1.0 (max).
    """

    strategy: StrategyType
    description: str
    chase_range: float  # How far monster will chase enemies (0 = no chase)
    heal_priority: bool  # Whether to prioritize healing allies
    follow_player: bool  # Whether to stay near the player
    aggression: float  # 0.0 = passive, 1.0 = max aggression


# Default behaviors for each strategy
STRATEGY_BEHAVIORS: dict[StrategyType, StrategyBehavior] = {
    StrategyType.ATTACK_NEAREST: StrategyBehavior(
        strategy=StrategyType.ATTACK_NEAREST,
        description="Attacks the closest enemy target",
        chase_range=5.0,
        heal_priority=False,
        follow_player=False,
        aggression=0.7,
    ),
    StrategyType.FOLLOW_PLAYER: StrategyBehavior(
        strategy=StrategyType.FOLLOW_PLAYER,
        description="Stays near the player and attacks nearby enemies",
        chase_range=3.0,
        heal_priority=False,
        follow_player=True,
        aggression=0.5,
    ),
    StrategyType.DEFENSIVE: StrategyBehavior(
        strategy=StrategyType.DEFENSIVE,
        description="Holds position and only attacks enemies in range",
        chase_range=0.0,
        heal_priority=False,
        follow_player=False,
        aggression=0.3,
    ),
    StrategyType.AGGRESSIVE: StrategyBehavior(
        strategy=StrategyType.AGGRESSIVE,
        description="Chases enemies aggressively across long distances",
        chase_range=15.0,
        heal_priority=False,
        follow_player=False,
        aggression=1.0,
    ),
    StrategyType.HEAL_LOWEST: StrategyBehavior(
        strategy=StrategyType.HEAL_LOWEST,
        description="Prioritizes healing the ally with lowest HP",
        chase_range=3.0,
        heal_priority=True,
        follow_player=True,
        aggression=0.2,
    ),
}


def get_strategy_behavior(strategy: StrategyType) -> StrategyBehavior:
    """Get the behavior profile for a strategy.

    Args:
        strategy: The strategy type to look up.

    Returns:
        The StrategyBehavior for the given strategy.
    """
    return STRATEGY_BEHAVIORS[strategy]


def select_target_by_strategy(
    strategy: StrategyType,
    attacker: Monster,
    allies: list[Monster],
    enemies: list[Monster],
    proficiency: float = 0.5,
) -> Monster | None:
    """Select a target based on strategy type and proficiency.

    Higher proficiency means better target selection.
    Low proficiency introduces suboptimal choices.

    Args:
        strategy: The strategy to use for selection.
        attacker: The monster making the selection.
        allies: Friendly monsters (excluding attacker).
        enemies: Enemy monsters.
        proficiency: 0.0-1.0 proficiency level (affects selection quality).

    Returns:
        Target monster, or None if no valid target.
    """
    # TODO: Use proficiency to introduce suboptimal targeting at low levels
    _ = proficiency

    active_enemies = [e for e in enemies if not e.is_fainted]
    active_allies = [a for a in allies if not a.is_fainted and a.monster_id != attacker.monster_id]

    if strategy == StrategyType.HEAL_LOWEST and active_allies:
        # Heal the ally with lowest HP percentage
        return min(
            active_allies,
            key=lambda m: m.current_hp / max(m.max_hp(), 1),
        )

    if not active_enemies:
        return None

    if strategy == StrategyType.ATTACK_NEAREST:
        # In backend simulation, "nearest" = first in list (spatial is Unity's job)
        return active_enemies[0]

    if strategy == StrategyType.AGGRESSIVE:
        # Target lowest HP enemy for fastest kills
        return min(active_enemies, key=lambda m: m.current_hp)

    if strategy == StrategyType.DEFENSIVE:
        # Target highest threat (highest attack)
        return max(
            active_enemies,
            key=lambda m: m.effective_stats().attack,
        )

    if strategy == StrategyType.FOLLOW_PLAYER:
        # Target nearest enemy (same as attack_nearest for backend)
        return active_enemies[0]

    # Fallback
    return active_enemies[0] if active_enemies else None
