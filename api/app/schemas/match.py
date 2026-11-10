from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MatchResult = Literal["WIN", "LOSS", "DRAW"]
DiceResult = Literal["WIN", "LOSS"]
TurnOrder = Literal["FIRST", "SECOND"]


class MatchCreate(BaseModel):
    my_leader_id: int = Field(gt=0)
    opponent_leader_id: int = Field(gt=0)
    opponent_user_id: int | None = Field(default=None, gt=0)
    opponent_name: str = Field(min_length=1, max_length=100)
    result: MatchResult
    dice_result: DiceResult
    turn_order: TurnOrder
    round_number: int | None = Field(default=None, gt=0)
    tournament_id: int | None = Field(default=None, gt=0)

    @field_validator("opponent_name")
    @classmethod
    def normalize_opponent_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Ime protivnika ne smije biti prazno")
        return normalized


class MatchUpdate(BaseModel):
    my_leader_id: int | None = Field(default=None, gt=0)
    opponent_leader_id: int | None = Field(default=None, gt=0)
    opponent_user_id: int | None = Field(default=None, gt=0)
    opponent_name: str | None = Field(default=None, min_length=1, max_length=100)
    result: MatchResult | None = None
    dice_result: DiceResult | None = None
    turn_order: TurnOrder | None = None
    round_number: int | None = Field(default=None, gt=0)
    tournament_id: int | None = Field(default=None, gt=0)

    @field_validator("opponent_name")
    @classmethod
    def normalize_opponent_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip()
        if not normalized:
            raise ValueError("Ime protivnika ne smije biti prazno")
        return normalized


class MatchResponse(BaseModel):
    id: int
    user_id: int
    my_leader_id: int
    opponent_leader_id: int
    opponent_user_id: int | None
    opponent_name: str
    result: MatchResult
    dice_result: DiceResult
    turn_order: TurnOrder
    round_number: int | None
    tournament_id: int | None
    played_at: datetime

    model_config = ConfigDict(from_attributes=True)
