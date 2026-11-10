from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Leader, Match


def _counts():
    return (
        func.count(Match.id).label("total_matches"),
        func.count().filter(Match.result == "WIN").label("wins"),
        func.count().filter(Match.result == "LOSS").label("losses"),
        func.count().filter(Match.result == "DRAW").label("draws"),
    )


async def overall(db: AsyncSession, user_id: int):
    result = await db.execute(select(*_counts()).where(Match.user_id == user_id))
    return result.one()


async def by_my_leader(db: AsyncSession, user_id: int, limit: int, offset: int):
    result = await db.execute(
        select(
            Match.my_leader_id,
            Leader.name,
            Leader.code,
            *_counts(),
        )
        .join(Leader, Leader.id == Match.my_leader_id)
        .where(Match.user_id == user_id)
        .group_by(Match.my_leader_id, Leader.name, Leader.code)
        .order_by(func.count(Match.id).desc(), Leader.code)
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def by_opponent_name(db: AsyncSession, user_id: int, limit: int, offset: int):
    normalized_name = func.lower(func.trim(Match.opponent_name))
    result = await db.execute(
        select(
            normalized_name.label("opponent_name"),
            func.min(func.trim(Match.opponent_name)).label("display_name"),
            *_counts(),
        )
        .where(Match.user_id == user_id)
        .group_by(normalized_name)
        .order_by(func.count(Match.id).desc(), normalized_name)
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def by_opponent_leader(db: AsyncSession, user_id: int, limit: int, offset: int):
    result = await db.execute(
        select(
            Match.opponent_leader_id,
            Leader.name,
            Leader.code,
            *_counts(),
        )
        .join(Leader, Leader.id == Match.opponent_leader_id)
        .where(Match.user_id == user_id)
        .group_by(Match.opponent_leader_id, Leader.name, Leader.code)
        .order_by(func.count(Match.id).desc(), Leader.code)
        .limit(limit)
        .offset(offset)
    )
    return result.all()


async def by_opponent_matchup(db: AsyncSession, user_id: int, limit: int, offset: int):
    normalized_name = func.lower(func.trim(Match.opponent_name))
    result = await db.execute(
        select(
            normalized_name.label("opponent_name"),
            func.min(func.trim(Match.opponent_name)).label("display_name"),
            Match.opponent_leader_id,
            Leader.name,
            Leader.code,
            *_counts(),
        )
        .join(Leader, Leader.id == Match.opponent_leader_id)
        .where(Match.user_id == user_id)
        .group_by(normalized_name, Match.opponent_leader_id, Leader.name, Leader.code)
        .order_by(func.count(Match.id).desc(), normalized_name, Leader.code)
        .limit(limit)
        .offset(offset)
    )
    return result.all()
