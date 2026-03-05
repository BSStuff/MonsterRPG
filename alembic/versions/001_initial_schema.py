"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-05 13:35:50.888803

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create all initial tables."""
    # --- players ---
    op.create_table(
        "players",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("supabase_user_id", sa.String(255), nullable=False, unique=True),
        sa.Column("username", sa.String(30), nullable=False),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("experience", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_players_supabase_user_id", "players", ["supabase_user_id"], unique=True)
    op.create_index("ix_players_username", "players", ["username"])

    # --- monsters ---
    op.create_table(
        "monsters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("species_id", sa.String(100), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("level", sa.Integer, nullable=False, server_default="1"),
        sa.Column("experience", sa.Integer, nullable=False, server_default="0"),
        sa.Column("bond_level", sa.Integer, nullable=False, server_default="0"),
        sa.Column("current_hp", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_fainted", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("equipped_skill_ids", postgresql.JSON, nullable=False, server_default="[]"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_monsters_player_id", "monsters", ["player_id"])
    op.create_index("ix_monsters_species_id", "monsters", ["species_id"])

    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(30), nullable=False, server_default="Team 1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_teams_player_id", "teams", ["player_id"])

    # --- team_members ---
    op.create_table(
        "team_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "team_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "monster_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monsters.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])
    op.create_index("ix_team_members_monster_id", "team_members", ["monster_id"])

    # --- game_states ---
    op.create_table(
        "game_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("save_data", postgresql.JSON, nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_game_states_player_id", "game_states", ["player_id"], unique=True)

    # --- economy_states ---
    op.create_table(
        "economy_states",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("gold", sa.Integer, nullable=False, server_default="0"),
        sa.Column("gems", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_economy_states_player_id", "economy_states", ["player_id"], unique=True)

    # --- transactions ---
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("currency_type", sa.String(10), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column("balance_after", sa.Integer, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_transactions_player_id", "transactions", ["player_id"])

    # --- premium_purchases ---
    op.create_table(
        "premium_purchases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("upgrade_id", sa.String(100), nullable=False),
        sa.Column("purchase_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_premium_purchases_player_id", "premium_purchases", ["player_id"])

    # --- subscriptions ---
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "player_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("players.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("tier", sa.String(20), nullable=False, server_default="none"),
        sa.Column("start_timestamp", sa.Float, nullable=False, server_default="0"),
        sa.Column("end_timestamp", sa.Float, nullable=False, server_default="0"),
        sa.Column("auto_renew", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_subscriptions_player_id", "subscriptions", ["player_id"], unique=True)


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table("subscriptions")
    op.drop_table("premium_purchases")
    op.drop_table("transactions")
    op.drop_table("economy_states")
    op.drop_table("game_states")
    op.drop_table("team_members")
    op.drop_table("teams")
    op.drop_table("monsters")
    op.drop_table("players")
