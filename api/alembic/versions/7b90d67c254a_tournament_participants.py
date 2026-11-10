"""Add tournament participation and selected leader.

Revision ID: 7b90d67c254a
Revises: 42e67b91c03d
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7b90d67c254a"
down_revision: str | Sequence[str] | None = "42e67b91c03d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tournament_participants",
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("leader_id", sa.Integer(), nullable=False),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["leader_id"],
            ["leaders.id"],
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("tournament_id", "user_id"),
    )
    op.create_index(
        "ix_tournament_participants_user_id",
        "tournament_participants",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tournament_participants_user_id", table_name="tournament_participants"
    )
    op.drop_table("tournament_participants")
