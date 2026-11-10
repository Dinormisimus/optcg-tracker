from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas.match import MatchCreate, MatchResponse, MatchUpdate
from app.services import match_service

router = APIRouter(prefix="/matches", tags=["Mečevi"])


@router.get("", response_model=list[MatchResponse])
async def list_matches(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[MatchResponse]:
    return await match_service.list_matches(db, user, limit, offset)


@router.get("/{match_id}", response_model=MatchResponse)
async def get_match(
    match_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> MatchResponse:
    return await match_service.get_match(db, user, match_id)


@router.post("", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    body: MatchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> MatchResponse:
    return await match_service.create_match(db, user, body)


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match(
    match_id: int,
    body: MatchUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> MatchResponse:
    return await match_service.update_match(db, user, match_id, body)


@router.delete("/{match_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_match(
    match_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Response:
    await match_service.delete_match(db, user, match_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
