from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.leader import Leader
    from app.models.tournament import Tournament
    from app.models.user import User


class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"

    tournament_id: Mapped[int] = mapped_column(
        ForeignKey("tournaments.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    leader_id: Mapped[int] = mapped_column(ForeignKey("leaders.id"), nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    tournament: Mapped["Tournament"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="tournament_participations")
    leader: Mapped["Leader"] = relationship()
