"""Crafting service — recipes, inventory, and life skills via game state persistence.

Bridges between API routers and the crafting/life_skills models.
All mutations follow the pattern: load game state -> modify -> save back.
"""

from __future__ import annotations

import uuid  # noqa: TC003 — used at runtime in function signatures
from typing import TYPE_CHECKING, Any

from sqlalchemy.ext.asyncio import AsyncSession  # noqa: TC002

from elements_rpg.economy.crafting import CraftingRecipe, execute_craft
from elements_rpg.economy.life_skills import LifeSkill, LifeSkillType
from elements_rpg.services.save_service import load_game_state, save_game_state

if TYPE_CHECKING:
    from elements_rpg.save_load import GameSaveData

# ---------------------------------------------------------------------------
# MVP Recipes — defined here since no recipe catalog module exists yet
# ---------------------------------------------------------------------------

MVP_RECIPES: dict[str, CraftingRecipe] = {
    "recipe_healing_salve": CraftingRecipe(
        recipe_id="recipe_healing_salve",
        name="Healing Salve",
        description="A basic healing item crafted from herbs.",
        required_materials={"mat_green_herb": 3},
        output_material_id="mat_healing_salve",
        output_quantity=1,
        required_skill_type="cooking",
        required_skill_level=1,
        craft_duration_seconds=15.0,
        xp_reward=15,
    ),
    "recipe_iron_ingot": CraftingRecipe(
        recipe_id="recipe_iron_ingot",
        name="Iron Ingot",
        description="Refined iron, useful for advanced crafting.",
        required_materials={"mat_iron_ore": 3, "mat_rough_stone": 1},
        output_material_id="mat_iron_ingot",
        output_quantity=1,
        required_skill_type="mining",
        required_skill_level=5,
        craft_duration_seconds=30.0,
        xp_reward=25,
    ),
    "recipe_crystal_lens": CraftingRecipe(
        recipe_id="recipe_crystal_lens",
        name="Crystal Lens",
        description="A polished lens made from crystal shards.",
        required_materials={"mat_crystal_shard": 2, "mat_luminous_gem": 1},
        output_material_id="mat_crystal_lens",
        output_quantity=1,
        required_skill_type="mining",
        required_skill_level=10,
        craft_duration_seconds=45.0,
        xp_reward=40,
    ),
    "recipe_meadow_potion": CraftingRecipe(
        recipe_id="recipe_meadow_potion",
        name="Meadow Potion",
        description="A fragrant potion brewed from meadow flowers and cave moss.",
        required_materials={"mat_meadow_flower": 2, "mat_cave_moss": 1},
        output_material_id="mat_meadow_potion",
        output_quantity=1,
        required_skill_type="cooking",
        required_skill_level=8,
        craft_duration_seconds=25.0,
        xp_reward=30,
    ),
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


async def _load_state_or_raise(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> GameSaveData:
    """Load game state, raising ValueError if no save exists."""
    state = await load_game_state(db, player_id)
    if state is None:
        raise ValueError(f"No save found for player {player_id}")
    return state


def _find_life_skill(
    state: GameSaveData,
    skill_id: str,
) -> LifeSkill | None:
    """Find a life skill in the save data by skill type string."""
    for skill in state.life_skills:
        if skill.skill_type.value == skill_id:
            return skill
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def get_recipes() -> list[dict[str, Any]]:
    """Get all available crafting recipes.

    Returns:
        List of recipe data dicts.
    """
    return [r.model_dump() for r in MVP_RECIPES.values()]


async def execute_craft_recipe(
    db: AsyncSession,
    player_id: uuid.UUID,
    recipe_id: str,
) -> dict[str, Any]:
    """Execute a crafting recipe — consume materials, produce output.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        recipe_id: The recipe to craft.

    Returns:
        Dict with craft result including output item and updated inventory.

    Raises:
        ValueError: If recipe not found, insufficient materials/skill, or no save.
    """
    recipe = MVP_RECIPES.get(recipe_id)
    if recipe is None:
        raise ValueError(f"Recipe '{recipe_id}' not found")

    state = await _load_state_or_raise(db, player_id)

    # Check life skill requirement
    if recipe.required_skill_type is not None:
        skill = _find_life_skill(state, recipe.required_skill_type)
        if skill is None or skill.level < recipe.required_skill_level:
            current_level = skill.level if skill else 0
            raise ValueError(
                f"Requires {recipe.required_skill_type} level "
                f"{recipe.required_skill_level}, have {current_level}"
            )

    success = execute_craft(state.inventory, recipe)
    if not success:
        raise ValueError(
            f"Insufficient materials for '{recipe.name}'. "
            f"Required: {recipe.required_materials}, "
            f"Have: {state.inventory.items}"
        )

    # Grant life skill XP for crafting
    if recipe.required_skill_type is not None:
        skill = _find_life_skill(state, recipe.required_skill_type)
        if skill is not None:
            skill.gain_experience(recipe.xp_reward)

    await save_game_state(db, player_id, state)
    return {
        "crafted": True,
        "recipe_id": recipe_id,
        "output_material_id": recipe.output_material_id,
        "output_quantity": recipe.output_quantity,
        "xp_granted": recipe.xp_reward,
        "inventory": state.inventory.items,
    }


async def get_inventory(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> dict[str, Any]:
    """Get the player's material inventory.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.

    Returns:
        Dict with items mapping (material_id -> quantity).
    """
    state = await _load_state_or_raise(db, player_id)
    return {"items": state.inventory.items}


async def get_life_skills(
    db: AsyncSession,
    player_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """Get the player's life skill levels and XP.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.

    Returns:
        List of life skill data dicts.
    """
    state = await _load_state_or_raise(db, player_id)
    return [skill.model_dump() for skill in state.life_skills]


async def grant_life_skill_xp(
    db: AsyncSession,
    player_id: uuid.UUID,
    skill_id: str,
    xp: int,
) -> dict[str, Any]:
    """Grant XP to a life skill and persist.

    Args:
        db: The async database session.
        player_id: The player's internal UUID.
        skill_id: The life skill type string (mining, cooking, strategy_training).
        xp: Amount of XP to grant (must be positive).

    Returns:
        Dict with updated skill data and levels gained.

    Raises:
        ValueError: If skill_id is invalid, xp is not positive, or no save.
    """
    # Validate skill_id
    try:
        LifeSkillType(skill_id)
    except ValueError as e:
        valid = [t.value for t in LifeSkillType]
        raise ValueError(f"Invalid skill_id '{skill_id}'. Valid options: {valid}") from e

    state = await _load_state_or_raise(db, player_id)
    skill = _find_life_skill(state, skill_id)
    if skill is None:
        raise ValueError(f"Life skill '{skill_id}' not found in player save data")

    old_level = skill.level
    levels_gained = skill.gain_experience(xp)

    await save_game_state(db, player_id, state)
    return {
        "skill_type": skill.skill_type.value,
        "level": skill.level,
        "experience": skill.experience,
        "old_level": old_level,
        "levels_gained": levels_gained,
    }
