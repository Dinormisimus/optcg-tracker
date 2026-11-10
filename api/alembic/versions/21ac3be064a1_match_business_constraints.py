"""Add match round constraints.

Revision ID: 21ac3be064a1
Revises: f67ad0988be4
Create Date: 2026-11-10
"""

from collections.abc import Sequence

from alembic import op

revision: str = "21ac3be064a1"
down_revision: str | Sequence[str] | None = "f67ad0988be4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_match_round_number_positive",
        "matches",
        "round_number IS NULL OR round_number > 0",
    )
    op.create_check_constraint(
        "ck_match_tournament_round_required",
        "matches",
        "tournament_id IS NULL OR round_number IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_match_tournament_round_required", "matches", type_="check")
    op.drop_constraint("ck_match_round_number_positive", "matches", type_="check")
