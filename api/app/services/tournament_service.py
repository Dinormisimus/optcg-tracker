from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import Tournament, User
from app.repositories import tournament_repo
from app.schemas.tournament import TournamentCreate, TournamentUpdate


async def list_tournaments(
    db: AsyncSession, limit: int, offset: int
) -> list[Tournament]:
    return await tournament_repo.list_tournaments(db, limit, offset)


async def get_tournament(db: AsyncSession, tournament_id: int) -> Tournament:
    tournament = await tournament_repo.get_by_id(db, tournament_id)
    if tournament is None:
        raise AppError("not_found", "Turnir nije pronađen", 404)
    return tournament


async def _get_manageable_tournament(
    db: AsyncSession, tournament_id: int, user: User
) -> Tournament:
    tournament = await get_tournament(db, tournament_id)
    if user.role != "super_admin" and tournament.organizer_id != user.id:
        raise AppError("forbidden", "Nemate pravo mijenjati ovaj turnir", 403)
    return tournament


async def create_tournament(
    db: AsyncSession, user: User, body: TournamentCreate
) -> Tournament:
    tournament = Tournament(organizer_id=user.id, **body.model_dump())
    db.add(tournament)
    await db.commit()
    await db.refresh(tournament)
    return tournament


async def update_tournament(
    db: AsyncSession, user: User, tournament_id: int, body: TournamentUpdate
) -> Tournament:
    tournament = await _get_manageable_tournament(db, tournament_id, user)
    changes = body.model_dump(exclude_unset=True)
    if any(value is None for value in changes.values()):
        raise AppError("invalid_tournament", "Polje ne smije biti null", 422)

    for field, value in changes.items():
        setattr(tournament, field, value)
    await db.commit()
    await db.refresh(tournament)
    return tournament


async def delete_tournament(db: AsyncSession, user: User, tournament_id: int) -> None:
    tournament = await _get_manageable_tournament(db, tournament_id, user)
    if await tournament_repo.has_matches(db, tournament_id):
        raise AppError(
            "tournament_has_matches",
            "Turnir koji ima zabilježene mečeve ne može se obrisati",
            409,
        )

    await db.delete(tournament)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            "tournament_has_matches",
            "Turnir koji ima zabilježene mečeve ne može se obrisati",
            409,
        )
