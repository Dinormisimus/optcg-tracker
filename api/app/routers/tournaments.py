from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models import User
from app.schemas.tournament import (
    MyTournamentResponse,
    TournamentCreate,
    TournamentEnrollmentResponse,
    TournamentParticipantResponse,
    TournamentParticipationCreate,
    TournamentParticipationUpdate,
    TournamentResponse,
    TournamentUpdate,
)
from app.services import tournament_participant_service, tournament_service

router = APIRouter(prefix="/tournaments", tags=["Turniri"])


@router.get("/mine", response_model=list[MyTournamentResponse])
async def list_my_tournaments(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[MyTournamentResponse]:
    return await tournament_participant_service.my_tournaments(db, user, limit, offset)


@router.get("", response_model=list[TournamentResponse])
async def list_tournaments(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TournamentResponse]:
    return await tournament_service.list_tournaments(db, limit, offset)


@router.get("/{tournament_id}", response_model=TournamentResponse)
async def get_tournament(
    tournament_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TournamentResponse:
    return await tournament_service.get_tournament(db, tournament_id)


@router.get(
    "/{tournament_id}/participants",
    response_model=list[TournamentParticipantResponse],
)
async def list_tournament_participants(
    tournament_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[TournamentParticipantResponse]:
    return await tournament_participant_service.list_participants(
        db, tournament_id, limit, offset
    )


@router.post(
    "/{tournament_id}/participants/me",
    response_model=TournamentEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_tournament(
    tournament_id: int,
    body: TournamentParticipationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TournamentEnrollmentResponse:
    return await tournament_participant_service.register(
        db, tournament_id, user, body.leader_id
    )


@router.get(
    "/{tournament_id}/participants/me",
    response_model=TournamentEnrollmentResponse,
)
async def get_my_tournament_registration(
    tournament_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TournamentEnrollmentResponse:
    return await tournament_participant_service.get_my_registration(
        db, tournament_id, user
    )


@router.patch(
    "/{tournament_id}/participants/me",
    response_model=TournamentEnrollmentResponse,
)
async def update_my_tournament_leader(
    tournament_id: int,
    body: TournamentParticipationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TournamentEnrollmentResponse:
    return await tournament_participant_service.update_leader(
        db, tournament_id, user, body.leader_id
    )


@router.delete(
    "/{tournament_id}/participants/me", status_code=status.HTTP_204_NO_CONTENT
)
async def leave_tournament(
    tournament_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    await tournament_participant_service.unregister(db, tournament_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("", response_model=TournamentResponse, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    body: TournamentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "super_admin"))],
) -> TournamentResponse:
    return await tournament_service.create_tournament(db, user, body)


@router.patch("/{tournament_id}", response_model=TournamentResponse)
async def update_tournament(
    tournament_id: int,
    body: TournamentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "super_admin"))],
) -> TournamentResponse:
    return await tournament_service.update_tournament(db, user, tournament_id, body)


@router.delete("/{tournament_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tournament(
    tournament_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(require_role("admin", "super_admin"))],
) -> Response:
    await tournament_service.delete_tournament(db, user, tournament_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
