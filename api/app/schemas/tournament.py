from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

TournamentFormat = Literal["SWISS", "CUSTOM"]


class TournamentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    format: TournamentFormat = "SWISS"


class TournamentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    format: TournamentFormat | None = None


class TournamentResponse(BaseModel):
    id: int
    name: str
    format: TournamentFormat
    organizer_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TournamentParticipationCreate(BaseModel):
    leader_id: int = Field(gt=0)


class TournamentParticipationUpdate(BaseModel):
    leader_id: int = Field(gt=0)


class TournamentParticipantResponse(BaseModel):
    tournament_id: int
    user_id: int
    username: str
    leader_id: int
    leader_name: str
    leader_code: str
    joined_at: datetime


class MyTournamentResponse(BaseModel):
    tournament_id: int
    tournament_name: str
    format: TournamentFormat
    organizer_id: int
    leader_id: int
    leader_name: str
    leader_code: str
    joined_at: datetime


class TournamentEnrollmentResponse(BaseModel):
    tournament_id: int
    user_id: int
    leader_id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)
