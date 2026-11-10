from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import Leader, TournamentParticipant, User
from app.repositories import tournament_participant_repo
from app.services.tournament_service import get_tournament


async def my_tournaments(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[dict]:
    rows = await tournament_participant_repo.list_for_user(db, user.id, limit, offset)
    return [
        {
            "tournament_id": row[0].tournament_id,
            "tournament_name": row[1],
            "format": row[2],
            "organizer_id": row[3],
            "leader_id": row[0].leader_id,
            "leader_name": row[4],
            "leader_code": row[5],
            "joined_at": row[0].joined_at,
        }
        for row in rows
    ]


async def list_participants(
    db: AsyncSession, tournament_id: int, limit: int, offset: int
) -> list[dict]:
    await get_tournament(db, tournament_id)
    rows = await tournament_participant_repo.list_for_tournament(
        db, tournament_id, limit, offset
    )
    return [
        {
            "tournament_id": row[0].tournament_id,
            "user_id": row[0].user_id,
            "username": row[1],
            "leader_id": row[0].leader_id,
            "leader_name": row[2],
            "leader_code": row[3],
            "joined_at": row[0].joined_at,
        }
        for row in rows
    ]


async def get_my_registration(
    db: AsyncSession, tournament_id: int, user: User
) -> TournamentParticipant:
    await get_tournament(db, tournament_id)
    participant = await tournament_participant_repo.get(db, tournament_id, user.id)
    if participant is None:
        raise AppError("not_registered", "Niste prijavljeni na ovaj turnir", 404)
    return participant


async def register(
    db: AsyncSession, tournament_id: int, user: User, leader_id: int
) -> TournamentParticipant:
    await get_tournament(db, tournament_id)
    if await db.get(Leader, leader_id) is None:
        raise AppError("leader_not_found", "Vođa nije pronađen", 404)
    if await tournament_participant_repo.get(db, tournament_id, user.id):
        raise AppError("already_registered", "Već ste prijavljeni na ovaj turnir", 409)

    participant = TournamentParticipant(
        tournament_id=tournament_id,
        user_id=user.id,
        leader_id=leader_id,
    )
    db.add(participant)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError("already_registered", "Već ste prijavljeni na ovaj turnir", 409)
    await db.refresh(participant)
    return participant


async def update_leader(
    db: AsyncSession, tournament_id: int, user: User, leader_id: int
) -> TournamentParticipant:
    await get_tournament(db, tournament_id)
    participant = await tournament_participant_repo.get(db, tournament_id, user.id)
    if participant is None:
        raise AppError("not_registered", "Niste prijavljeni na ovaj turnir", 404)
    if await db.get(Leader, leader_id) is None:
        raise AppError("leader_not_found", "Vođa nije pronađen", 404)
    if (
        participant.leader_id != leader_id
        and await tournament_participant_repo.has_matches(db, tournament_id, user.id)
    ):
        raise AppError(
            "leader_locked",
            "Vođu nije moguće promijeniti nakon prvog odigranog meča na turniru",
            409,
        )

    participant.leader_id = leader_id
    await db.commit()
    await db.refresh(participant)
    return participant


async def unregister(db: AsyncSession, tournament_id: int, user: User) -> None:
    await get_tournament(db, tournament_id)
    participant = await tournament_participant_repo.get(db, tournament_id, user.id)
    if participant is None:
        raise AppError("not_registered", "Niste prijavljeni na ovaj turnir", 404)
    if await tournament_participant_repo.has_matches(db, tournament_id, user.id):
        raise AppError(
            "participation_has_matches",
            "Ne možete odjaviti turnir nakon što ste odigrali meč",
            409,
        )
    await db.delete(participant)
    await db.commit()
