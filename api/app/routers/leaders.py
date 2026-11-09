from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, require_role
from app.models import Leader, User
from app.schemas import LeaderResponse, LeaderCreate

router = APIRouter(prefix="/leaders", tags=["Leaders"])


@router.get("", response_model=List[LeaderResponse])
async def list_leaders(
    color: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Dohvaća sve dostupne vođe uz opcionalno filtriranje po boji."""
    stmt = select(Leader)
    if color:
        stmt = stmt.where(Leader.color.ilike(f"%{color}%"))
    
    result = await db.execute(stmt.order_by(Leader.code))
    return result.scalars().all()


@router.post("", response_model=LeaderResponse, status_code=status.HTTP_201_CREATED)
async def create_leader(
    leader_in: LeaderCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_role("admin", "super_admin")),
):
    """Omogućuje unošenje novog vođe (za administratore)."""
    stmt = select(Leader).where(Leader.code == leader_in.code)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Vođa s ovim kodom već postoji."
        )

    new_leader = Leader(**leader_in.model_dump())
    db.add(new_leader)
    await db.commit()
    await db.refresh(new_leader)
    return new_leader