"""SQLAlchemy models for economy state, transactions, and premium purchases."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003 — required at runtime by SQLAlchemy Mapped[]

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from elements_rpg.db.base import Base


class EconomyStateDB(Base):
    """Player's current gold and gem balances.

    One row per player, updated on every currency change.
    """

    __tablename__ = "economy_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    gold: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gems: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<EconomyStateDB player={self.player_id} gold={self.gold} gems={self.gems}>"


class TransactionDB(Base):
    """Immutable ledger entry for a currency transaction."""

    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    currency_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        doc="Either 'gold' or 'gems'",
    )
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Positive = credit, negative = debit",
    )
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<TransactionDB id={self.id} {self.currency_type} "
            f"{self.amount:+d} reason={self.reason!r}>"
        )


class PremiumPurchaseDB(Base):
    """Tracks how many times a player has bought each premium upgrade."""

    __tablename__ = "premium_purchases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    player_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    upgrade_id: Mapped[str] = mapped_column(String(100), nullable=False)
    purchase_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<PremiumPurchaseDB player={self.player_id} "
            f"upgrade={self.upgrade_id!r} count={self.purchase_count}>"
        )
