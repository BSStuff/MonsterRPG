"""Monster data models — stats, levels, bonds, and skill slots."""

from enum import StrEnum

from pydantic import BaseModel, Field

from elements_rpg.config import MAX_EQUIPPED_SKILLS, MAX_MONSTER_LEVEL


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


def xp_for_level(level: int) -> int:
    """Calculate XP required to reach a given level.

    Uses a power-curve formula that scales smoothly: ~100 XP for level 2,
    ~346 for level 3, increasing steeply at higher levels.

    Args:
        level: The target level (must be >= 1).

    Returns:
        XP required to reach that level. Level 1 requires 0 XP.

    Raises:
        ValueError: If level is less than 1.
    """
    if level < 1:
        raise ValueError(f"Level must be >= 1, got {level}")
    if level == 1:
        return 0
    return int(100 * (level**1.5))


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
        """Calculate level-scaled stats with bond bonus.

        Level scaling adds 5% per level above 1. Bond bonus adds 0.2% per
        bond level (max 20% at bond 100), applied after level scaling.

        Returns:
            A StatBlock with stats scaled by level and bond.
        """
        level_scale = 1.0 + (self.level - 1) * 0.05
        bond_multiplier = 1.0 + (self.bond_level * 0.002)
        base = self.species.base_stats
        combined = level_scale * bond_multiplier
        return StatBlock(
            hp=round(base.hp * combined),
            attack=round(base.attack * combined),
            defense=round(base.defense * combined),
            speed=round(base.speed * combined),
            magic_attack=round(base.magic_attack * combined),
            magic_defense=round(base.magic_defense * combined),
        )

    def max_hp(self) -> int:
        """Return the monster's maximum HP at current level and bond.

        Returns:
            The HP value from effective_stats().
        """
        return self.effective_stats().hp

    def gain_experience(self, xp: int) -> list[int]:
        """Add XP and process any level-ups.

        Can gain multiple levels at once if enough XP is provided. Leftover
        XP after leveling is retained. Does not modify current_hp.

        Args:
            xp: Amount of experience to add (must be >= 0).

        Returns:
            List of new levels gained (e.g. [2, 3] if leveled from 1 to 3).
            Empty list if no levels were gained.

        Raises:
            ValueError: If xp is negative.
        """
        if xp < 0:
            raise ValueError(f"XP must be non-negative, got {xp}")

        if self.level >= MAX_MONSTER_LEVEL:
            return []

        self.experience += xp
        levels_gained: list[int] = []

        while self.level < MAX_MONSTER_LEVEL:
            next_level = self.level + 1
            xp_needed = xp_for_level(next_level)
            if self.experience >= xp_needed:
                self.level = next_level
                self.experience -= xp_needed
                levels_gained.append(next_level)
            else:
                break

        # Cap leftover XP at max level
        if self.level >= MAX_MONSTER_LEVEL:
            self.experience = 0

        return levels_gained

    def gain_bond(self, amount: int) -> int:
        """Increase the bond level with the player.

        Args:
            amount: Bond points to add (must be >= 0).

        Returns:
            The new bond_level after the increase.

        Raises:
            ValueError: If amount is negative.
        """
        if amount < 0:
            raise ValueError(f"Bond amount must be non-negative, got {amount}")
        self.bond_level = min(100, self.bond_level + amount)
        return self.bond_level

    def can_learn_skill(self, skill_id: str) -> bool:
        """Check if this monster's species can learn a given skill.

        Args:
            skill_id: The skill identifier to check.

        Returns:
            True if the skill is in the species' learnable_skill_ids.
        """
        return skill_id in self.species.learnable_skill_ids

    def equip_skill(self, skill_id: str) -> bool:
        """Equip a skill to this monster.

        The skill must be in the species' learnable_skill_ids and there must
        be an open slot (max 4 equipped). Duplicate equips are rejected.

        Args:
            skill_id: The skill identifier to equip.

        Returns:
            True if the skill was successfully equipped, False otherwise.
        """
        if not self.can_learn_skill(skill_id):
            return False
        if len(self.equipped_skill_ids) >= MAX_EQUIPPED_SKILLS:
            return False
        if skill_id in self.equipped_skill_ids:
            return False
        self.equipped_skill_ids.append(skill_id)
        return True

    def unequip_skill(self, skill_id: str) -> bool:
        """Remove a skill from this monster's equipped list.

        Args:
            skill_id: The skill identifier to unequip.

        Returns:
            True if the skill was removed, False if it was not equipped.
        """
        if skill_id not in self.equipped_skill_ids:
            return False
        self.equipped_skill_ids.remove(skill_id)
        return True
