from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db, require_role
from app.models import User
from app.schemas.tournament import (
    TournamentCreate,
    TournamentResponse,
    TournamentUpdate,
)
from app.services import tournament_service

router = APIRouter(prefix="/tournaments", tags=["Turniri"])


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
