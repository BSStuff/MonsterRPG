"""MVP Area definitions and drop table system."""

from pydantic import BaseModel, Field, model_validator

from monster_rpg.economy.crafting import Material
from monster_rpg.economy.manager import Area, AreaDifficulty


class DropTableEntry(BaseModel):
    """A single entry in an area's drop table."""

    material_id: str = Field(min_length=1)
    drop_chance: float = Field(gt=0.0, le=1.0)
    min_quantity: int = Field(default=1, ge=1)
    max_quantity: int = Field(default=1, ge=1)
    difficulty_required: AreaDifficulty | None = Field(
        default=None, description="Minimum difficulty for this drop"
    )

    @model_validator(mode="after")
    def validate_quantity_range(self) -> "DropTableEntry":
        if self.min_quantity > self.max_quantity:
            raise ValueError(
                f"min_quantity ({self.min_quantity}) cannot exceed "
                f"max_quantity ({self.max_quantity})"
            )
        return self


class AreaDropTable(BaseModel):
    """Drop table for an area -- what materials can drop and at what rates."""

    area_id: str = Field(min_length=1)
    entries: list[DropTableEntry] = Field(default_factory=list)

    def get_drops_for_difficulty(self, difficulty: AreaDifficulty) -> list[DropTableEntry]:
        """Get drops available at a specific difficulty level."""
        difficulty_order = [
            AreaDifficulty.EASY,
            AreaDifficulty.MEDIUM,
            AreaDifficulty.HARD,
            AreaDifficulty.BOSS,
        ]
        current_idx = difficulty_order.index(difficulty)
        return [
            e
            for e in self.entries
            if e.difficulty_required is None
            or difficulty_order.index(e.difficulty_required) <= current_idx
        ]


# ==========================================
# MVP AREA DEFINITIONS
# ==========================================

# --- Area 1: Verdant Meadows (Starter area) ---
VERDANT_MEADOWS = Area(
    area_id="area_verdant_meadows",
    name="Verdant Meadows",
    difficulty=AreaDifficulty.EASY,
    recommended_level=1,
    monster_species_ids=[
        "species_leaflet",
        "species_ember_pup",
        "species_breeze_sprite",
        "species_pebble_crab",
        "species_dewdrop_slime",
        "species_meadow_fox",
    ],
    material_drop_ids=[
        "mat_green_herb",
        "mat_rough_stone",
        "mat_soft_fur",
        "mat_meadow_flower",
    ],
    description="A peaceful grassland teeming with gentle monsters. Perfect for beginning tamers.",
)

# --- Area 2: Crystal Caverns (Mid-level area) ---
CRYSTAL_CAVERNS = Area(
    area_id="area_crystal_caverns",
    name="Crystal Caverns",
    difficulty=AreaDifficulty.MEDIUM,
    recommended_level=15,
    monster_species_ids=[
        "species_crystal_bat",
        "species_magma_wyrm",
        "species_aqua_serpent",
        "species_shadow_moth",
        "species_geo_golem",
        "species_prism_fairy",
    ],
    material_drop_ids=[
        "mat_crystal_shard",
        "mat_cave_moss",
        "mat_iron_ore",
        "mat_luminous_gem",
    ],
    description="Deep underground caverns lit by glowing crystals. Stronger monsters dwell here.",
)

# All MVP areas
MVP_AREAS: dict[str, Area] = {
    VERDANT_MEADOWS.area_id: VERDANT_MEADOWS,
    CRYSTAL_CAVERNS.area_id: CRYSTAL_CAVERNS,
}

# ==========================================
# MVP MATERIALS
# ==========================================

MVP_MATERIALS: dict[str, Material] = {
    "mat_green_herb": Material(
        material_id="mat_green_herb",
        name="Green Herb",
        description="A common medicinal herb.",
        sell_price=5,
    ),
    "mat_rough_stone": Material(
        material_id="mat_rough_stone",
        name="Rough Stone",
        description="A chunk of unrefined stone.",
        sell_price=3,
    ),
    "mat_soft_fur": Material(
        material_id="mat_soft_fur",
        name="Soft Fur",
        description="Soft fur from meadow creatures.",
        sell_price=8,
    ),
    "mat_meadow_flower": Material(
        material_id="mat_meadow_flower",
        name="Meadow Flower",
        description="A colorful wildflower with faint magical aroma.",
        sell_price=10,
    ),
    "mat_crystal_shard": Material(
        material_id="mat_crystal_shard",
        name="Crystal Shard",
        description="A fragment of cave crystal pulsing with energy.",
        sell_price=20,
    ),
    "mat_cave_moss": Material(
        material_id="mat_cave_moss",
        name="Cave Moss",
        description="Bioluminescent moss from deep caverns.",
        sell_price=15,
    ),
    "mat_iron_ore": Material(
        material_id="mat_iron_ore",
        name="Iron Ore",
        description="Raw iron ore, useful for crafting.",
        sell_price=12,
    ),
    "mat_luminous_gem": Material(
        material_id="mat_luminous_gem",
        name="Luminous Gem",
        description="A rare gem that glows in the dark.",
        sell_price=50,
    ),
}

# ==========================================
# DROP TABLES
# ==========================================

VERDANT_MEADOWS_DROPS = AreaDropTable(
    area_id="area_verdant_meadows",
    entries=[
        DropTableEntry(
            material_id="mat_green_herb",
            drop_chance=0.6,
            min_quantity=1,
            max_quantity=3,
        ),
        DropTableEntry(
            material_id="mat_rough_stone",
            drop_chance=0.4,
            min_quantity=1,
            max_quantity=2,
        ),
        DropTableEntry(
            material_id="mat_soft_fur",
            drop_chance=0.3,
            min_quantity=1,
            max_quantity=1,
        ),
        DropTableEntry(
            material_id="mat_meadow_flower",
            drop_chance=0.15,
            min_quantity=1,
            max_quantity=1,
            difficulty_required=AreaDifficulty.MEDIUM,
        ),
    ],
)

CRYSTAL_CAVERNS_DROPS = AreaDropTable(
    area_id="area_crystal_caverns",
    entries=[
        DropTableEntry(
            material_id="mat_cave_moss",
            drop_chance=0.5,
            min_quantity=1,
            max_quantity=2,
        ),
        DropTableEntry(
            material_id="mat_iron_ore",
            drop_chance=0.35,
            min_quantity=1,
            max_quantity=2,
        ),
        DropTableEntry(
            material_id="mat_crystal_shard",
            drop_chance=0.2,
            min_quantity=1,
            max_quantity=1,
        ),
        DropTableEntry(
            material_id="mat_luminous_gem",
            drop_chance=0.05,
            min_quantity=1,
            max_quantity=1,
            difficulty_required=AreaDifficulty.HARD,
        ),
    ],
)

MVP_DROP_TABLES: dict[str, AreaDropTable] = {
    VERDANT_MEADOWS.area_id: VERDANT_MEADOWS_DROPS,
    CRYSTAL_CAVERNS.area_id: CRYSTAL_CAVERNS_DROPS,
}
