from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Match


async def list_for_user(
    db: AsyncSession, user_id: int, limit: int, offset: int
) -> list[Match]:
    result = await db.execute(
        select(Match)
        .where(Match.user_id == user_id)
        .order_by(Match.played_at.desc(), Match.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_for_user(db: AsyncSession, match_id: int, user_id: int) -> Match | None:
    result = await db.execute(
        select(Match).where(Match.id == match_id, Match.user_id == user_id)
    )
    return result.scalar_one_or_none()


def add(db: AsyncSession, match: Match) -> None:
    db.add(match)
