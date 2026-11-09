from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models import Leader, User
from app.schemas import LeaderResponse

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
    leader_data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Omogućuje unesenje novog vođe (za admnistratore)."""
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Nemate ovlasti za dodavanje vođa.")
        
    stmt = select(Leader).where(Leader.code == leader_data["code"])
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Vođa s ovim kodom već postoji.")

    new_leader = Leader(**leader_data)
    db.add(new_leader)
    await db.commit()
    await db.refresh(new_leader)
    return new_leader