from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Match, Tournament


async def list_tournaments(
    db: AsyncSession, limit: int, offset: int
) -> list[Tournament]:
    result = await db.execute(
        select(Tournament)
        .order_by(Tournament.created_at.desc(), Tournament.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_by_id(db: AsyncSession, tournament_id: int) -> Tournament | None:
    return await db.get(Tournament, tournament_id)


async def has_matches(db: AsyncSession, tournament_id: int) -> bool:
    count = await db.scalar(
        select(func.count())
        .select_from(Match)
        .where(Match.tournament_id == tournament_id)
    )
    return bool(count)
