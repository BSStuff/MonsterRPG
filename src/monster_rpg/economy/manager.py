"""Economy manager — handles resource tracking, areas, and material inventories."""

from enum import StrEnum

from pydantic import BaseModel, Field


class AreaDifficulty(StrEnum):
    """Difficulty levels for game areas."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    BOSS = "boss"


class Area(BaseModel):
    """A game area/zone that players explore.

    Attributes:
        area_id: Unique area identifier.
        name: Display name of the area.
        difficulty: Difficulty tier.
        recommended_level: Suggested player level for this area.
        monster_species_ids: IDs of monsters that spawn in this area.
        material_drop_ids: IDs of materials that drop in this area.
        description: Text description of the area.
    """

    area_id: str = Field(min_length=1, description="Unique area identifier")
    name: str = Field(min_length=1, max_length=50)
    difficulty: AreaDifficulty
    recommended_level: int = Field(ge=1, le=100)
    monster_species_ids: list[str] = Field(default_factory=list)
    material_drop_ids: list[str] = Field(default_factory=list)
    description: str
