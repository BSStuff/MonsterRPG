"""Monster data models — stats, levels, bonds, and skill slots."""

from enum import StrEnum

from pydantic import BaseModel, Field

from monster_rpg.config import MAX_EQUIPPED_SKILLS, MAX_MONSTER_LEVEL


class Element(StrEnum):
    """Monster element types."""

    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    WIND = "wind"
    NEUTRAL = "neutral"


class Rarity(StrEnum):
    """Monster rarity tiers."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


class StatBlock(BaseModel):
    """Base stats for a monster.

    Attributes:
        hp: Hit points.
        attack: Physical attack power.
        defense: Physical defense.
        speed: Action speed.
        magic_attack: Magic attack power.
        magic_defense: Magic defense.
    """

    hp: int = Field(ge=1, description="Hit points")
    attack: int = Field(ge=0, description="Physical attack power")
    defense: int = Field(ge=0, description="Physical defense")
    speed: int = Field(ge=0, description="Action speed")
    magic_attack: int = Field(ge=0, description="Magic attack power")
    magic_defense: int = Field(ge=0, description="Magic defense")


class MonsterSpecies(BaseModel):
    """Template for a monster species (shared across all instances).

    Attributes:
        species_id: Unique species identifier.
        name: Display name of the species.
        element: Elemental type.
        rarity: Rarity tier.
        base_stats: Base stat block before level scaling.
        passive_trait: Passive ability name.
        passive_description: What the passive does.
        learnable_skill_ids: Skills this species can learn.
    """

    species_id: str = Field(min_length=1, description="Unique species identifier")
    name: str = Field(min_length=1, max_length=50)
    element: Element
    rarity: Rarity
    base_stats: StatBlock
    passive_trait: str = Field(description="Passive ability name")
    passive_description: str = Field(description="What the passive does")
    learnable_skill_ids: list[str] = Field(
        default_factory=list,
        description="Skills this species can learn",
    )


class Monster(BaseModel):
    """An individual monster instance owned by a player.

    Attributes:
        monster_id: Unique instance identifier.
        species: The species template for this monster.
        level: Current level (1-100).
        experience: Accumulated XP.
        bond_level: Bond with player (0-100).
        equipped_skill_ids: IDs of currently equipped skills (max 4).
        current_hp: Current HP in combat.
        is_fainted: Whether the monster has fainted.
    """

    monster_id: str = Field(min_length=1, description="Unique instance identifier")
    species: MonsterSpecies
    level: int = Field(default=1, ge=1, le=MAX_MONSTER_LEVEL)
    experience: int = Field(default=0, ge=0)
    bond_level: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Bond with player 0-100",
    )
    equipped_skill_ids: list[str] = Field(
        default_factory=list,
        max_length=MAX_EQUIPPED_SKILLS,
    )
    current_hp: int = Field(ge=0, description="Current HP in combat")
    is_fainted: bool = Field(default=False)

    def effective_stats(self) -> StatBlock:
        """Calculate level-scaled stats. Simple linear scaling for MVP.

        Returns:
            A StatBlock with stats scaled by the monster's current level.
            Each level adds 5% to base stats.
        """
        scale = 1.0 + (self.level - 1) * 0.05
        base = self.species.base_stats
        return StatBlock(
            hp=round(base.hp * scale),
            attack=round(base.attack * scale),
            defense=round(base.defense * scale),
            speed=round(base.speed * scale),
            magic_attack=round(base.magic_attack * scale),
            magic_defense=round(base.magic_defense * scale),
        )
