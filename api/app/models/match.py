from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.leader import Leader
    from app.models.tournament import Tournament
    from app.models.user import User


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        CheckConstraint("result IN ('WIN', 'LOSS', 'DRAW')", name="ck_match_result"),
        CheckConstraint("dice_result IN ('WIN', 'LOSS')", name="ck_dice_result"),
        CheckConstraint("turn_order IN ('FIRST', 'SECOND')", name="ck_turn_order"),
        CheckConstraint(
            "round_number IS NULL OR round_number > 0",
            name="ck_match_round_number_positive",
        ),
        CheckConstraint(
            "tournament_id IS NULL OR round_number IS NOT NULL",
            name="ck_match_tournament_round_required",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )

    my_leader_id: Mapped[int] = mapped_column(ForeignKey("leaders.id"), nullable=False)
    opponent_leader_id: Mapped[int] = mapped_column(
        ForeignKey("leaders.id"), nullable=False
    )

    opponent_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    opponent_name: Mapped[str] = mapped_column(String(100), nullable=False)

    result: Mapped[str] = mapped_column(String(10), nullable=False)
    dice_result: Mapped[str] = mapped_column(String(10), nullable=False)
    turn_order: Mapped[str] = mapped_column(String(10), nullable=False)

    round_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tournament_id: Mapped[int | None] = mapped_column(
        ForeignKey("tournaments.id"), nullable=True
    )
    played_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User", foreign_keys=[user_id], back_populates="matches"
    )
    my_leader: Mapped["Leader"] = relationship("Leader", foreign_keys=[my_leader_id])
    opponent_leader: Mapped["Leader"] = relationship(
        "Leader", foreign_keys=[opponent_leader_id]
    )
    tournament: Mapped["Tournament | None"] = relationship(
        "Tournament", back_populates="matches"
    )
