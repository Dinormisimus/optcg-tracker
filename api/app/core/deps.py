from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.errors import AppError
from app.models import User
from app.services import auth_service

security_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user(
    auth: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    if auth is None:
        raise AppError("invalid_credentials", "Nedostaju autentifikacijski podaci", 401)
    return await auth_service.get_user_from_token(db, auth.credentials, "access")


def require_role(*allowed_roles: str):
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise AppError("forbidden", "Nemate dozvolu za ovu radnju", 403)
        return current_user

    return role_checker
