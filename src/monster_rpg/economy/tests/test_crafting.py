"""Tests for the crafting system — materials, recipes, inventory, crafting."""

import pytest
from pydantic import ValidationError

from monster_rpg.economy.crafting import (
    CraftingRecipe,
    Inventory,
    Material,
    can_craft,
    execute_craft,
)

# --- Helpers ---


def _make_material(**overrides: object) -> Material:
    defaults: dict[str, object] = {
        "material_id": "mat_wood",
        "name": "Wood",
    }
    defaults.update(overrides)
    return Material(**defaults)


def _make_recipe(**overrides: object) -> CraftingRecipe:
    defaults: dict[str, object] = {
        "recipe_id": "recipe_plank",
        "name": "Wooden Plank",
        "required_materials": {"mat_wood": 3},
        "output_material_id": "mat_plank",
    }
    defaults.update(overrides)
    return CraftingRecipe(**defaults)


# --- Material Tests ---


class TestMaterial:
    def test_valid_construction(self) -> None:
        mat = _make_material()
        assert mat.material_id == "mat_wood"
        assert mat.name == "Wood"
        assert mat.max_stack == 999
        assert mat.sell_price == 0

    def test_custom_fields(self) -> None:
        mat = _make_material(
            description="A sturdy log",
            max_stack=100,
            sell_price=5,
        )
        assert mat.description == "A sturdy log"
        assert mat.max_stack == 100
        assert mat.sell_price == 5

    def test_empty_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_material(material_id="")

    def test_empty_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_material(name="")

    def test_long_name_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_material(name="X" * 51)

    def test_negative_sell_price_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_material(sell_price=-1)

    def test_zero_max_stack_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_material(max_stack=0)


# --- CraftingRecipe Tests ---


class TestCraftingRecipe:
    def test_valid_construction(self) -> None:
        recipe = _make_recipe()
        assert recipe.recipe_id == "recipe_plank"
        assert recipe.required_materials == {"mat_wood": 3}
        assert recipe.output_material_id == "mat_plank"
        assert recipe.output_quantity == 1
        assert recipe.craft_duration_seconds == 30.0
        assert recipe.xp_reward == 10

    def test_custom_recipe(self) -> None:
        recipe = _make_recipe(
            required_skill_type="mining",
            required_skill_level=5,
            output_quantity=2,
            craft_duration_seconds=60.0,
            xp_reward=25,
        )
        assert recipe.required_skill_type == "mining"
        assert recipe.required_skill_level == 5
        assert recipe.output_quantity == 2

    def test_empty_recipe_id_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_recipe(recipe_id="")

    def test_zero_output_quantity_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_recipe(output_quantity=0)

    def test_zero_duration_rejected(self) -> None:
        with pytest.raises(ValidationError):
            _make_recipe(craft_duration_seconds=0)


# --- Inventory Tests ---


class TestInventory:
    def test_empty_inventory(self) -> None:
        inv = Inventory()
        assert inv.get_quantity("mat_wood") == 0

    def test_add_material(self) -> None:
        inv = Inventory()
        result = inv.add_material("mat_wood", 5)
        assert result == 5
        assert inv.get_quantity("mat_wood") == 5

    def test_add_material_stacks(self) -> None:
        inv = Inventory()
        inv.add_material("mat_wood", 3)
        result = inv.add_material("mat_wood", 7)
        assert result == 10

    def test_add_material_zero_raises(self) -> None:
        inv = Inventory()
        with pytest.raises(ValueError, match="positive"):
            inv.add_material("mat_wood", 0)

    def test_add_material_negative_raises(self) -> None:
        inv = Inventory()
        with pytest.raises(ValueError, match="positive"):
            inv.add_material("mat_wood", -1)

    def test_remove_material_success(self) -> None:
        inv = Inventory(items={"mat_wood": 10})
        assert inv.remove_material("mat_wood", 3) is True
        assert inv.get_quantity("mat_wood") == 7

    def test_remove_material_insufficient(self) -> None:
        inv = Inventory(items={"mat_wood": 2})
        assert inv.remove_material("mat_wood", 5) is False
        assert inv.get_quantity("mat_wood") == 2

    def test_remove_material_not_present(self) -> None:
        inv = Inventory()
        assert inv.remove_material("mat_wood", 1) is False

    def test_remove_material_zero_raises(self) -> None:
        inv = Inventory(items={"mat_wood": 5})
        with pytest.raises(ValueError, match="positive"):
            inv.remove_material("mat_wood", 0)

    def test_remove_material_negative_raises(self) -> None:
        inv = Inventory(items={"mat_wood": 5})
        with pytest.raises(ValueError, match="positive"):
            inv.remove_material("mat_wood", -1)

    def test_remove_material_cleans_up_zero(self) -> None:
        inv = Inventory(items={"mat_wood": 3})
        inv.remove_material("mat_wood", 3)
        assert "mat_wood" not in inv.items

    def test_has_materials_true(self) -> None:
        inv = Inventory(items={"mat_wood": 5, "mat_stone": 3})
        assert inv.has_materials({"mat_wood": 3, "mat_stone": 2}) is True

    def test_has_materials_false(self) -> None:
        inv = Inventory(items={"mat_wood": 1})
        assert inv.has_materials({"mat_wood": 5}) is False

    def test_has_materials_missing_item(self) -> None:
        inv = Inventory()
        assert inv.has_materials({"mat_wood": 1}) is False

    def test_has_materials_empty_requirements(self) -> None:
        inv = Inventory()
        assert inv.has_materials({}) is True


# --- Crafting Function Tests ---


class TestCrafting:
    def test_can_craft_sufficient(self) -> None:
        inv = Inventory(items={"mat_wood": 10})
        recipe = _make_recipe(required_materials={"mat_wood": 3})
        assert can_craft(inv, recipe) is True

    def test_can_craft_insufficient(self) -> None:
        inv = Inventory(items={"mat_wood": 1})
        recipe = _make_recipe(required_materials={"mat_wood": 3})
        assert can_craft(inv, recipe) is False

    def test_can_craft_empty_inventory(self) -> None:
        inv = Inventory()
        recipe = _make_recipe(required_materials={"mat_wood": 1})
        assert can_craft(inv, recipe) is False

    def test_execute_craft_success(self) -> None:
        inv = Inventory(items={"mat_wood": 5})
        recipe = _make_recipe(
            required_materials={"mat_wood": 3},
            output_material_id="mat_plank",
            output_quantity=2,
        )
        assert execute_craft(inv, recipe) is True
        assert inv.get_quantity("mat_wood") == 2
        assert inv.get_quantity("mat_plank") == 2

    def test_execute_craft_consumes_all_inputs(self) -> None:
        inv = Inventory(items={"mat_wood": 3, "mat_stone": 2})
        recipe = _make_recipe(
            required_materials={"mat_wood": 3, "mat_stone": 2},
            output_material_id="mat_axe",
        )
        assert execute_craft(inv, recipe) is True
        assert "mat_wood" not in inv.items
        assert "mat_stone" not in inv.items
        assert inv.get_quantity("mat_axe") == 1

    def test_execute_craft_fails_gracefully(self) -> None:
        inv = Inventory(items={"mat_wood": 1})
        recipe = _make_recipe(required_materials={"mat_wood": 5})
        assert execute_craft(inv, recipe) is False
        assert inv.get_quantity("mat_wood") == 1  # unchanged
