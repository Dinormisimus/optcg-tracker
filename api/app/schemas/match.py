from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
