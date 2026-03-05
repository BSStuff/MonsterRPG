"""Crafting system — recipes and material transformation."""

from pydantic import BaseModel, Field


class Material(BaseModel):
    """A material/resource in the game."""

    material_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="")
    max_stack: int = Field(default=999, ge=1)
    sell_price: int = Field(default=0, ge=0, description="Gold value when sold")


class CraftingRecipe(BaseModel):
    """A recipe for crafting items."""

    recipe_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=50)
    description: str = Field(default="")
    required_materials: dict[str, int] = Field(description="material_id -> quantity needed")
    output_material_id: str = Field(min_length=1)
    output_quantity: int = Field(default=1, ge=1)
    required_skill_type: str | None = Field(default=None, description="Life skill type required")
    required_skill_level: int = Field(default=1, ge=1)
    craft_duration_seconds: float = Field(default=30.0, gt=0)
    xp_reward: int = Field(default=10, ge=0)


class Inventory(BaseModel):
    """Player's material inventory."""

    items: dict[str, int] = Field(
        default_factory=dict,
        description="material_id -> quantity",
    )

    def get_quantity(self, material_id: str) -> int:
        """Get quantity of a material."""
        return self.items.get(material_id, 0)

    def add_material(self, material_id: str, quantity: int) -> int:
        """Add materials to inventory.

        Returns:
            New total quantity.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        current = self.items.get(material_id, 0)
        self.items[material_id] = current + quantity
        return self.items[material_id]

    def remove_material(self, material_id: str, quantity: int) -> bool:
        """Remove materials from inventory.

        Returns:
            True if removed, False if insufficient quantity.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        current = self.items.get(material_id, 0)
        if current < quantity:
            return False
        new_qty = current - quantity
        if new_qty == 0:
            del self.items[material_id]
        else:
            self.items[material_id] = new_qty
        return True

    def has_materials(self, requirements: dict[str, int]) -> bool:
        """Check if inventory has all required materials."""
        return all(self.get_quantity(mat_id) >= qty for mat_id, qty in requirements.items())


def can_craft(inventory: Inventory, recipe: CraftingRecipe) -> bool:
    """Check if a recipe can be crafted with current inventory."""
    return inventory.has_materials(recipe.required_materials)


def execute_craft(inventory: Inventory, recipe: CraftingRecipe) -> bool:
    """Execute a crafting recipe — consume materials, produce output.

    Returns:
        True if crafted successfully, False if insufficient materials.
    """
    if not can_craft(inventory, recipe):
        return False

    # Remove input materials
    for mat_id, qty in recipe.required_materials.items():
        inventory.remove_material(mat_id, qty)

    # Add output
    inventory.add_material(recipe.output_material_id, recipe.output_quantity)
    return True
