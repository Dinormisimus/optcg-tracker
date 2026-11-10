from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Leader


async def get_by_code(db: AsyncSession, code: str) -> Leader | None:
    result = await db.execute(select(Leader).where(Leader.code == code))
    return result.scalar_one_or_none()


async def list_leaders(
    db: AsyncSession, color: str | None, limit: int, offset: int
) -> list[Leader]:
    stmt = select(Leader)
    if color:
        stmt = stmt.where(Leader.color.ilike(f"%{color}%"))
    result = await db.execute(stmt.order_by(Leader.code).limit(limit).offset(offset))
    return list(result.scalars().all())


def add(db: AsyncSession, leader: Leader) -> Leader:
    db.add(leader)
    return leader