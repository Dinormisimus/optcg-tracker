from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models import Leader, User
from app.repositories import leader_repo
from app.schemas import LeaderCreate, LeaderResponse

router = APIRouter(prefix="/leaders", tags=["Leaders"])


@router.get("", response_model=list[LeaderResponse])
async def list_leaders(
    db: Annotated[AsyncSession, Depends(get_db)],
    color: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[LeaderResponse]:
    """Dohvaća sve dostupne vođe uz opcionalno filtriranje po boji."""
    return await leader_repo.list_leaders(db, color, limit, offset)


@router.post("", response_model=LeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_leader(
    leader_in: LeaderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_role("admin", "super_admin"))],
):
    """Omogućuje unošenje novog vođe (za administratore)."""
    stmt = select(Leader).where(Leader.code == leader_in.code)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vođa s ovim kodom već postoji.",
        )

    new_leader = Leader(**leader_in.model_dump())
    db.add(new_leader)
    await db.commit()
    await db.refresh(new_leader)
    return new_leader
