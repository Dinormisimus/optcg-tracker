from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.repositories import stats_repo


def _counts(row) -> dict[str, int | float | None]:
    wins = row.wins
    losses = row.losses
    draws = row.draws
    decided_matches = wins + losses
    return {
        "total_matches": row.total_matches,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "decided_matches": decided_matches,
        "win_rate": round(wins / decided_matches * 100, 2) if decided_matches else None,
    }


async def overall(db: AsyncSession, user: User) -> dict[str, int | float | None]:
    return _counts(await stats_repo.overall(db, user.id))


async def by_my_leader(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[dict]:
    rows = await stats_repo.by_my_leader(db, user.id, limit, offset)
    return [
        {
            "leader_id": row.my_leader_id,
            "leader_name": row.name,
            "leader_code": row.code,
            **_counts(row),
        }
        for row in rows
    ]


async def by_opponent_name(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[dict]:
    rows = await stats_repo.by_opponent_name(db, user.id, limit, offset)
    return [
        {
            "opponent_name": row.display_name,
            **_counts(row),
        }
        for row in rows
    ]


async def by_opponent_leader(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[dict]:
    rows = await stats_repo.by_opponent_leader(db, user.id, limit, offset)
    return [
        {
            "opponent_leader_id": row.opponent_leader_id,
            "opponent_leader_name": row.name,
            "opponent_leader_code": row.code,
            **_counts(row),
        }
        for row in rows
    ]


async def by_opponent_matchup(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[dict]:
    rows = await stats_repo.by_opponent_matchup(db, user.id, limit, offset)
    return [
        {
            "opponent_name": row.display_name,
            "opponent_leader_id": row.opponent_leader_id,
            "opponent_leader_name": row.name,
            "opponent_leader_code": row.code,
            **_counts(row),
        }
        for row in rows
    ]
