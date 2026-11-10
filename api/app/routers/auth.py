from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, get_db
from app.models import User
from app.schemas import LoginRequest, Token, UserResponse
from app.schemas.auth import RefreshTokenRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Autentifikacija"])


@router.post("/login", response_model=Token)
async def login(
    form_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    user = await auth_service.authenticate_user(
        db, form_data.username, form_data.password
    )
    access_token, refresh_token = auth_service.create_tokens(user)
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    body: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Token:
    access_token, refresh_token = await auth_service.refresh_tokens(
        db, body.refresh_token
    )
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user
