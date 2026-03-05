"""SQLAlchemy model for full game state (hybrid JSON storage)."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003 — required at runtime by SQLAlchemy Mapped[]

from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from elements_rpg.db.base import Base


class GameStateDB(Base):
    """Atomic game save stored as JSON.

    Stores the full GameSaveData Pydantic model serialized to JSON.
    Player and monster tables provide queryable relational access to
    key fields; this table is the source of truth for save/load.
    """

    __tablename__ = "game_states"

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
    save_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        doc="Full GameSaveData serialized as JSON",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Save format version for migration support",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        return f"<GameStateDB id={self.id} player={self.player_id} version={self.version}>"
