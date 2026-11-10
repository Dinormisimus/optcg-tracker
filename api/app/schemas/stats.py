from pydantic import BaseModel


class StatsSummary(BaseModel):
    total_matches: int
    wins: int
    losses: int
    draws: int
    decided_matches: int
    win_rate: float | None


class LeaderStats(StatsSummary):
    leader_id: int
    leader_name: str
    leader_code: str


class OpponentStats(StatsSummary):
    opponent_name: str


class OpponentLeaderStats(StatsSummary):
    opponent_leader_id: int
    opponent_leader_name: str
    opponent_leader_code: str


class MatchupStats(StatsSummary):
    opponent_name: str
    opponent_leader_id: int
    opponent_leader_name: str
    opponent_leader_code: str
