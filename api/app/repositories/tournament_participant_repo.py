from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Leader,
    Match,
    Tournament,
    TournamentParticipant,
    User,
)


async def get(
    db: AsyncSession, tournament_id: int, user_id: int
) -> TournamentParticipant | None:
    return await db.get(TournamentParticipant, (tournament_id, user_id))


async def list_for_tournament(
    db: AsyncSession, tournament_id: int, limit: int, offset: int
):
    result = await db.execute(
        select(TournamentParticipant, User.username, Leader.name, Leader.code)
        .join(User, User.id == TournamentParticipant.user_id)
        .join(Leader, Leader.id == TournamentParticipant.leader_id)
        .where(TournamentParticipant.tournament_id == tournament_id)
        .order_by(User.username, TournamentParticipant.user_id)
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def list_for_user(db: AsyncSession, user_id: int, limit: int, offset: int):
    result = await db.execute(
        select(
            TournamentParticipant,
            Tournament.name,
            Tournament.format,
            Tournament.organizer_id,
            Leader.name,
            Leader.code,
        )
        .join(Tournament, Tournament.id == TournamentParticipant.tournament_id)
        .join(Leader, Leader.id == TournamentParticipant.leader_id)
        .where(TournamentParticipant.user_id == user_id)
        .order_by(Tournament.created_at.desc(), Tournament.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def has_matches(db: AsyncSession, tournament_id: int, user_id: int) -> bool:
    count = await db.scalar(
        select(func.count())
        .select_from(Match)
        .where(
            Match.tournament_id == tournament_id,
            Match.user_id == user_id,
        )
    )
    return bool(count)
