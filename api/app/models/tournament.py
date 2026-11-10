from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.tournament_participant import TournamentParticipant


class Tournament(Base):
    __tablename__ = "tournaments"
    __table_args__ = (
        CheckConstraint("format IN ('SWISS', 'CUSTOM')", name="ck_tournament_format"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="SWISS")
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    matches: Mapped[list["Match"]] = relationship("Match", back_populates="tournament")
    participants: Mapped[list["TournamentParticipant"]] = relationship(
        back_populates="tournament", cascade="all, delete-orphan"
    )
