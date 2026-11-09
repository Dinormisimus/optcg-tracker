from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, ForeignKey, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class Tournament(Base):
    __tablename__ = "tournaments"
    __table_args__ = (
        CheckConstraint("format IN ('SWISS', 'CUSTOM')", name="ck_tournament_format"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="SWISS")
    organizer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    matches: Mapped[List["Match"]] = relationship("Match", back_populates="tournament")