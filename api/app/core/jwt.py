from datetime import datetime, timedelta, timezone

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings

__all__ = [
    "ExpiredSignatureError",
    "InvalidTokenError",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
]

ALGORITHM = "HS256"


def create_access_token(user_id: int, role: str) -> str:
    """Kratkotrajan token koji putuje uz svaki zahtjev."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    """Dugotrajan token koji se šalje samo na /auth/refresh; nosi najmanje."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Provjerava potpis, istek i izdavatelja; vraća sadržaj tokena.

    Istekli token podiže ExpiredSignatureError, svaki drugi neispravan
    token InvalidTokenError. Prvi je podvrsta drugoga, pa se hvata prvi.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=[ALGORITHM],  # nikad algoritam iz zaglavlja samog tokena
        issuer=settings.JWT_ISSUER,
        options={"require": ["exp", "sub", "iss", "type"]},
    )