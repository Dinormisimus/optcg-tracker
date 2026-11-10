from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict[str, str]:
    try:
        result = await db.execute(text("SELECT version()"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Baza podataka nije dostupna",
        ) from exc

    return {"status": "ok", "database": result.scalar_one()}
