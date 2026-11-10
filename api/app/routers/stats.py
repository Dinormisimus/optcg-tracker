from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.stats import (
    LeaderStats,
    MatchupStats,
    OpponentLeaderStats,
    OpponentStats,
    StatsSummary,
)
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["Statistika"])


@router.get("/overall", response_model=StatsSummary)
async def get_overall_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> StatsSummary:
    return await stats_service.overall(db, user)


@router.get("/leaders", response_model=list[LeaderStats])
async def get_leader_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[LeaderStats]:
    return await stats_service.by_my_leader(db, user, limit, offset)


@router.get("/opponents", response_model=list[OpponentStats])
async def get_opponent_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[OpponentStats]:
    return await stats_service.by_opponent_name(db, user, limit, offset)


@router.get("/opponent-leaders", response_model=list[OpponentLeaderStats])
async def get_opponent_leader_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[OpponentLeaderStats]:
    return await stats_service.by_opponent_leader(db, user, limit, offset)


@router.get("/matchups", response_model=list[MatchupStats])
async def get_matchup_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[MatchupStats]:
    return await stats_service.by_opponent_matchup(db, user, limit, offset)
