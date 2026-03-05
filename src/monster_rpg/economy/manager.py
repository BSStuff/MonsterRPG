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


class CurrencyTransaction(BaseModel):
    """Record of a currency transaction."""

    transaction_id: str = Field(min_length=1)
    currency_type: str = Field(pattern=r"^(gold|gems)$")
    amount: int  # positive = credit, negative = debit
    reason: str = Field(min_length=1)
    balance_after: int = Field(ge=0)


class EconomyManager:
    """Manages player economy — gold, gems, transactions."""

    def __init__(self) -> None:
        self.transaction_log: list[CurrencyTransaction] = []

    def spend_gold(self, player_gold: int, amount: int, reason: str) -> tuple[bool, int]:
        """Attempt to spend gold.

        Returns:
            (success, new_balance)
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if player_gold < amount:
            return False, player_gold
        new_balance = player_gold - amount
        self.transaction_log.append(
            CurrencyTransaction(
                transaction_id=f"gold_{len(self.transaction_log)}",
                currency_type="gold",
                amount=-amount,
                reason=reason,
                balance_after=new_balance,
            )
        )
        return True, new_balance

    def earn_gold(self, player_gold: int, amount: int, reason: str) -> int:
        """Add gold to player balance.

        Returns:
            New balance.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        new_balance = player_gold + amount
        self.transaction_log.append(
            CurrencyTransaction(
                transaction_id=f"gold_{len(self.transaction_log)}",
                currency_type="gold",
                amount=amount,
                reason=reason,
                balance_after=new_balance,
            )
        )
        return new_balance

    def spend_gems(self, player_gems: int, amount: int, reason: str) -> tuple[bool, int]:
        """Attempt to spend premium currency (gems).

        Returns:
            (success, new_balance)
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if player_gems < amount:
            return False, player_gems
        new_balance = player_gems - amount
        self.transaction_log.append(
            CurrencyTransaction(
                transaction_id=f"gems_{len(self.transaction_log)}",
                currency_type="gems",
                amount=-amount,
                reason=reason,
                balance_after=new_balance,
            )
        )
        return True, new_balance

    def earn_gems(self, player_gems: int, amount: int, reason: str) -> int:
        """Add gems. Returns new balance."""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        new_balance = player_gems + amount
        self.transaction_log.append(
            CurrencyTransaction(
                transaction_id=f"gems_{len(self.transaction_log)}",
                currency_type="gems",
                amount=amount,
                reason=reason,
                balance_after=new_balance,
            )
        )
        return new_balance
