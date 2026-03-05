"""Team system — monster team composition and management."""

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from monster_rpg.config import MAX_TEAM_SIZE
from monster_rpg.monsters.models import Monster


class TeamRole(StrEnum):
    """Suggested team roles."""

    TANK = "tank"
    OFF_TANK = "off_tank"
    DPS = "dps"
    SUPPORT = "support"
    FLEX = "flex"


class TeamSlot(BaseModel):
    """A slot in the team with an assigned monster and optional role.

    Attributes:
        monster_id: Unique monster instance ID occupying this slot.
        role: Optional suggested role for this slot.
        position: Zero-based position index in the team (0-5).
    """

    monster_id: str = Field(min_length=1)
    role: TeamRole | None = Field(default=None)
    position: int = Field(ge=0, le=5)


class Team(BaseModel):
    """A team of up to 6 monsters.

    Attributes:
        team_id: Unique team identifier.
        name: Display name for the team.
        slots: List of team slots with assigned monsters.
    """

    team_id: str = Field(min_length=1)
    name: str = Field(default="Team 1", min_length=1, max_length=30)
    slots: list[TeamSlot] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_team_size(self) -> "Team":
        """Ensure team does not exceed MAX_TEAM_SIZE."""
        if len(self.slots) > MAX_TEAM_SIZE:
            raise ValueError(f"Team cannot exceed {MAX_TEAM_SIZE} monsters")
        return self

    @model_validator(mode="after")
    def validate_no_duplicate_monsters(self) -> "Team":
        """Ensure no duplicate monster IDs in the team."""
        ids = [s.monster_id for s in self.slots]
        if len(ids) != len(set(ids)):
            raise ValueError("Team cannot contain duplicate monster IDs")
        return self

    @model_validator(mode="after")
    def validate_no_duplicate_positions(self) -> "Team":
        """Ensure no duplicate positions in the team."""
        positions = [s.position for s in self.slots]
        if len(positions) != len(set(positions)):
            raise ValueError("Team slots cannot share positions")
        return self

    @property
    def size(self) -> int:
        """Return the number of monsters on the team."""
        return len(self.slots)

    @property
    def is_full(self) -> bool:
        """Return True if the team has MAX_TEAM_SIZE monsters."""
        return self.size >= MAX_TEAM_SIZE

    @property
    def is_empty(self) -> bool:
        """Return True if the team has no monsters."""
        return self.size == 0

    @property
    def monster_ids(self) -> list[str]:
        """Return ordered list of monster IDs on the team."""
        return [s.monster_id for s in self.slots]

    def add_monster(self, monster_id: str, role: TeamRole | None = None) -> bool:
        """Add a monster to the team.

        Args:
            monster_id: The monster instance ID to add.
            role: Optional role assignment for this monster.

        Returns:
            True if the monster was added, False if the team is full
            or the monster is already on the team.
        """
        if self.is_full:
            return False
        if monster_id in self.monster_ids:
            return False
        position = self.size
        self.slots.append(TeamSlot(monster_id=monster_id, role=role, position=position))
        return True

    def remove_monster(self, monster_id: str) -> bool:
        """Remove a monster from the team.

        Remaining monsters are re-indexed to maintain contiguous positions.

        Args:
            monster_id: The monster instance ID to remove.

        Returns:
            True if the monster was removed, False if not found.
        """
        for i, slot in enumerate(self.slots):
            if slot.monster_id == monster_id:
                self.slots.pop(i)
                for j, s in enumerate(self.slots):
                    s.position = j
                return True
        return False

    def reorder(self, monster_ids: list[str]) -> bool:
        """Reorder the team by providing monster IDs in desired order.

        Must contain exactly the same IDs as the current team.

        Args:
            monster_ids: Monster IDs in the new desired order.

        Returns:
            True if reorder succeeded, False if IDs don't match.
        """
        if sorted(monster_ids) != sorted(self.monster_ids):
            return False
        id_to_slot = {s.monster_id: s for s in self.slots}
        self.slots = []
        for i, mid in enumerate(monster_ids):
            slot = id_to_slot[mid]
            slot.position = i
            self.slots.append(slot)
        return True

    def set_role(self, monster_id: str, role: TeamRole | None) -> bool:
        """Set a role for a monster on the team.

        Args:
            monster_id: The monster instance ID.
            role: The role to assign, or None to clear the role.

        Returns:
            True if the role was set, False if the monster is not on the team.
        """
        for slot in self.slots:
            if slot.monster_id == monster_id:
                slot.role = role
                return True
        return False

    def get_monsters_by_role(self, role: TeamRole) -> list[str]:
        """Get monster IDs with a specific role.

        Args:
            role: The role to filter by.

        Returns:
            List of monster IDs assigned to that role.
        """
        return [s.monster_id for s in self.slots if s.role == role]

    def get_team_monsters(self, monster_registry: dict[str, Monster]) -> list[Monster]:
        """Get actual Monster objects for the team from a registry.

        Monsters not found in the registry are silently skipped.

        Args:
            monster_registry: Mapping of monster_id to Monster instances.

        Returns:
            List of Monster objects in team order.
        """
        return [monster_registry[mid] for mid in self.monster_ids if mid in monster_registry]
