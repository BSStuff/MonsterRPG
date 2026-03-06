"""Damage calculation logic for combat."""

from elements_rpg.monsters.models import Element, Monster
from elements_rpg.skills.progression import Skill, SkillType

# Type effectiveness chart: {(attacker_element, defender_element): multiplier}
# 2.0 = super effective, 0.5 = not effective, 0.0 = immune, 1.0 = neutral (omitted)
ELEMENT_CHART: dict[tuple[Element, Element], float] = {
    # Fire: strong vs Grass, Ice, Wind; weak vs Water, Rock, Ground
    (Element.FIRE, Element.GRASS): 2.0,
    (Element.FIRE, Element.ICE): 2.0,
    (Element.FIRE, Element.WIND): 2.0,
    (Element.FIRE, Element.WATER): 0.5,
    (Element.FIRE, Element.ROCK): 0.5,
    (Element.FIRE, Element.FIRE): 0.5,
    # Water: strong vs Fire, Rock, Ground; weak vs Grass, Electric, Water
    (Element.WATER, Element.FIRE): 2.0,
    (Element.WATER, Element.ROCK): 2.0,
    (Element.WATER, Element.GROUND): 2.0,
    (Element.WATER, Element.GRASS): 0.5,
    (Element.WATER, Element.ELECTRIC): 0.5,
    (Element.WATER, Element.WATER): 0.5,
    # Grass: strong vs Water, Ground, Rock; weak vs Fire, Ice, Wind, Grass
    (Element.GRASS, Element.WATER): 2.0,
    (Element.GRASS, Element.GROUND): 2.0,
    (Element.GRASS, Element.ROCK): 2.0,
    (Element.GRASS, Element.FIRE): 0.5,
    (Element.GRASS, Element.ICE): 0.5,
    (Element.GRASS, Element.WIND): 0.5,
    (Element.GRASS, Element.GRASS): 0.5,
    # Electric: strong vs Water, Wind; weak vs Ground (immune), Grass, Electric
    (Element.ELECTRIC, Element.WATER): 2.0,
    (Element.ELECTRIC, Element.WIND): 2.0,
    (Element.ELECTRIC, Element.GROUND): 0.0,  # immune
    (Element.ELECTRIC, Element.GRASS): 0.5,
    (Element.ELECTRIC, Element.ELECTRIC): 0.5,
    # Wind: strong vs Grass, Ground; weak vs Rock, Electric, Fire
    (Element.WIND, Element.GRASS): 2.0,
    (Element.WIND, Element.GROUND): 2.0,
    (Element.WIND, Element.ROCK): 0.5,
    (Element.WIND, Element.ELECTRIC): 0.5,
    (Element.WIND, Element.FIRE): 0.5,
    # Ground: strong vs Fire, Electric, Rock; weak vs Water, Grass, Ice
    (Element.GROUND, Element.FIRE): 2.0,
    (Element.GROUND, Element.ELECTRIC): 2.0,
    (Element.GROUND, Element.ROCK): 2.0,
    (Element.GROUND, Element.WATER): 0.5,
    (Element.GROUND, Element.GRASS): 0.5,
    (Element.GROUND, Element.ICE): 0.5,
    # Rock: strong vs Fire, Ice, Wind; weak vs Water, Grass, Ground
    (Element.ROCK, Element.FIRE): 2.0,
    (Element.ROCK, Element.ICE): 2.0,
    (Element.ROCK, Element.WIND): 2.0,
    (Element.ROCK, Element.WATER): 0.5,
    (Element.ROCK, Element.GRASS): 0.5,
    (Element.ROCK, Element.GROUND): 0.5,
    # Dark: strong vs Light; weak vs Dark (self-resist)
    (Element.DARK, Element.LIGHT): 2.0,
    (Element.DARK, Element.DARK): 0.5,
    # Light: strong vs Dark; weak vs Light (self-resist)
    (Element.LIGHT, Element.DARK): 2.0,
    (Element.LIGHT, Element.LIGHT): 0.5,
    # Ice: strong vs Grass, Ground, Wind; weak vs Fire, Rock, Water, Ice
    (Element.ICE, Element.GRASS): 2.0,
    (Element.ICE, Element.GROUND): 2.0,
    (Element.ICE, Element.WIND): 2.0,
    (Element.ICE, Element.FIRE): 0.5,
    (Element.ICE, Element.ROCK): 0.5,
    (Element.ICE, Element.WATER): 0.5,
    (Element.ICE, Element.ICE): 0.5,
}


def get_element_multiplier(
    attack_element: Element,
    defender_types: tuple[Element, Element | None],
) -> float:
    """Calculate type effectiveness multiplier for an attack against a defender.

    For dual-typed defenders, multiply both matchups:
    - 2.0 * 2.0 = 4.0 (double super effective)
    - 2.0 * 0.5 = 1.0 (cancels out)
    - 0.0 * anything = 0.0 (immunity takes precedence)

    Args:
        attack_element: The element of the attacking skill.
        defender_types: Tuple of (primary_type, secondary_type_or_None).

    Returns:
        The damage multiplier.
    """
    primary, secondary = defender_types
    mult = ELEMENT_CHART.get((attack_element, primary), 1.0)
    if secondary is not None:
        mult *= ELEMENT_CHART.get((attack_element, secondary), 1.0)
    return mult


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

    # Element effectiveness against defender's types
    defender_types = defender.species.types
    element_mult = get_element_multiplier(skill.element, defender_types)

    # STAB (Same Type Attack Bonus) — 1.5x if skill element matches either attacker type
    attacker_types = attacker.species.types
    stab = 1.5 if skill.element in (attacker_types[0], attacker_types[1]) else 1.0

    # Final calculation
    damage = int(base * element_mult * stab * random_factor)
    return max(damage, 1)  # Minimum 1 damage
