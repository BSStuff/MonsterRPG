"""Damage calculation logic for combat."""

from monster_rpg.monsters.models import Element, Monster
from monster_rpg.skills.progression import Skill, SkillType

# Element effectiveness matrix
# Key = (attacker_element, defender_element), Value = multiplier
ELEMENT_CHART: dict[tuple[Element, Element], float] = {
    (Element.FIRE, Element.WIND): 1.5,
    (Element.FIRE, Element.WATER): 0.5,
    (Element.WATER, Element.FIRE): 1.5,
    (Element.WATER, Element.EARTH): 0.5,
    (Element.EARTH, Element.WATER): 1.5,
    (Element.EARTH, Element.WIND): 0.5,
    (Element.WIND, Element.EARTH): 1.5,
    (Element.WIND, Element.FIRE): 0.5,
    # Neutral has no advantages or disadvantages
}


def get_element_multiplier(attacker_element: Element, defender_element: Element) -> float:
    """Get the element effectiveness multiplier.

    Args:
        attacker_element: The element of the attacking skill.
        defender_element: The element of the defending monster.

    Returns:
        The damage multiplier (0.5 for not effective, 1.0 for neutral, 1.5 for
        super effective).
    """
    return ELEMENT_CHART.get((attacker_element, defender_element), 1.0)


def calculate_damage(
    attacker: Monster,
    defender: Monster,
    skill: Skill,
    random_factor: float = 1.0,
) -> int:
    """Calculate damage dealt by attacker to defender using a skill.

    Uses a classic RPG formula: level factor * skill power * offense/defense ratio,
    modified by element effectiveness, STAB, and skill level bonus.

    Args:
        attacker: The attacking monster.
        defender: The defending monster.
        skill: The skill being used.
        random_factor: Random variance (0.85-1.0 typically). Default 1.0 for
            deterministic testing.

    Returns:
        The damage dealt (minimum 1).
    """
    atk_stats = attacker.effective_stats()
    def_stats = defender.effective_stats()

    # Physical vs Special based on skill type
    if skill.skill_type in (SkillType.ATTACK,):
        offense = atk_stats.attack
        defense = def_stats.defense
    else:
        offense = atk_stats.magic_attack
        defense = def_stats.magic_defense

    # Base damage formula (inspired by classic RPG formulas)
    # Level factor + offense/defense ratio + skill effective power
    level_factor = (2 * attacker.level / 5) + 2
    stat_ratio = offense / max(defense, 1)  # Prevent division by zero
    base = (level_factor * skill.effective_power() * stat_ratio) / 50 + 2

    # Element effectiveness
    element_mult = get_element_multiplier(skill.element, defender.species.element)

    # STAB (Same Type Attack Bonus) — 1.5x if skill element matches monster element
    stab = 1.5 if skill.element == attacker.species.element else 1.0

    # Final calculation
    damage = int(base * element_mult * stab * random_factor)
    return max(damage, 1)  # Minimum 1 damage
