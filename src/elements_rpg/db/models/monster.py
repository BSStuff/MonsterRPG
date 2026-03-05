"""SQLAlchemy model for owned monster instances."""

from __future__ import annotations

import uuid
from datetime import datetime  # noqa: TC003 — required at runtime by SQLAlchemy Mapped[]

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from elements_rpg.db.base import Base


class MonsterDB(Base):
    """Relational monster instance owned by a player.

    Stores key queryable fields (species, level, bond) relationally.
    equipped_skill_ids stored as JSON array for flexibility.
    """

    __tablename__ = "monsters"

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
    species_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    experience: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    bond_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_hp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_fainted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    equipped_skill_ids: Mapped[list[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<MonsterDB id={self.id} species={self.species_id!r} "
            f"level={self.level} player={self.player_id}>"
        )
