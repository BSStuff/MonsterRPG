"""SQLAlchemy model for player subscriptions."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003 — required at runtime by SQLAlchemy Mapped[]

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from elements_rpg.db.base import Base


class SubscriptionDB(Base):
    """Player's active subscription status.

    One row per player. Tier is 'none' when no subscription is active.
    """

    __tablename__ = "subscriptions"

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
    tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="none",
        doc="Subscription tier: none, monthly, quarterly, annual",
    )
    start_timestamp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
        doc="Unix timestamp when subscription started",
    )
    end_timestamp: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0,
        doc="Unix timestamp when subscription expires",
    )
    auto_renew: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<SubscriptionDB player={self.player_id} "
            f"tier={self.tier!r} auto_renew={self.auto_renew}>"
        )
