"""Allow tournament matches without a recorded round.

Revision ID: 42e67b91c03d
Revises: 21ac3be064a1
Create Date: 2026-11-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "42e67b91c03d"
down_revision: str | Sequence[str] | None = "21ac3be064a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("ck_match_tournament_round_required", "matches", type_="check")


def downgrade() -> None:
    op.create_check_constraint(
        "ck_match_tournament_round_required",
        "matches",
        "tournament_id IS NULL OR round_number IS NOT NULL",
    )
