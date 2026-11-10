from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import Leader, Match, Tournament, User
from app.repositories import match_repo, tournament_participant_repo
from app.schemas.match import MatchCreate, MatchUpdate


async def _validate_references(
    db: AsyncSession, user: User, values: dict[str, object]
) -> None:
    leader_ids = {
        values[key] for key in ("my_leader_id", "opponent_leader_id") if key in values
    }
    for leader_id in leader_ids:
        if await db.get(Leader, leader_id) is None:
            raise AppError("leader_not_found", "Vođa nije pronađen", 404)

    if "opponent_user_id" in values and values["opponent_user_id"] is not None:
        opponent_id = values["opponent_user_id"]
        if opponent_id == user.id:
            raise AppError(
                "invalid_opponent", "Ne možete biti sami sebi protivnik", 400
            )
        if await db.get(User, opponent_id) is None:
            raise AppError(
                "opponent_not_found", "Protivnički korisnik nije pronađen", 404
            )

    if (
        "tournament_id" in values
        and values["tournament_id"] is not None
        and await db.get(Tournament, values["tournament_id"]) is None
    ):
        raise AppError("tournament_not_found", "Turnir nije pronađen", 404)


async def _validate_tournament_leaders(
    db: AsyncSession,
    user: User,
    *,
    tournament_id: int | None,
    my_leader_id: int,
) -> None:
    if tournament_id is None:
        return

    participant = await tournament_participant_repo.get(db, tournament_id, user.id)
    if participant is None:
        raise AppError(
            "not_registered",
            "Prijavite se na turnir prije unosa turnirskog meča",
            409,
        )
    if participant.leader_id != my_leader_id:
        raise AppError(
            "tournament_leader_mismatch",
            "Meč mora koristiti Leadera odabranog pri prijavi na turnir",
            409,
        )


async def list_matches(
    db: AsyncSession, user: User, limit: int, offset: int
) -> list[Match]:
    return await match_repo.list_for_user(db, user.id, limit, offset)


async def get_match(db: AsyncSession, user: User, match_id: int) -> Match:
    match = await match_repo.get_for_user(db, match_id, user.id)
    if match is None:
        raise AppError("not_found", "Meč nije pronađen", 404)
    return match


async def create_match(db: AsyncSession, user: User, body: MatchCreate) -> Match:
    values = body.model_dump()
    await _validate_references(db, user, values)
    await _validate_tournament_leaders(
        db,
        user,
        tournament_id=values["tournament_id"],
        my_leader_id=values["my_leader_id"],
    )

    match = Match(user_id=user.id, **values)
    match_repo.add(db, match)
    await db.commit()
    await db.refresh(match)
    return match


async def update_match(
    db: AsyncSession, user: User, match_id: int, body: MatchUpdate
) -> Match:
    match = await get_match(db, user, match_id)
    changes = body.model_dump(exclude_unset=True)
    for key, value in changes.items():
        if key not in {"round_number", "tournament_id"} and value is None:
            raise AppError("invalid_match", f"Polje {key} ne smije biti null", 422)

    await _validate_references(db, user, changes)
    await _validate_tournament_leaders(
        db,
        user,
        tournament_id=changes.get("tournament_id", match.tournament_id),
        my_leader_id=changes.get("my_leader_id", match.my_leader_id),
    )

    for key, value in changes.items():
        setattr(match, key, value)
    await db.commit()
    await db.refresh(match)
    return match


async def delete_match(db: AsyncSession, user: User, match_id: int) -> None:
    match = await get_match(db, user, match_id)
    await db.delete(match)
    await db.commit()
