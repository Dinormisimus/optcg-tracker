from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.jwt import (
    ExpiredSignatureError,
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories import user_repo
from app.schemas.user import UserCreate

INVALID_CREDENTIALS = "Neispravno korisničko ime ili lozinka"
ACCOUNT_ALREADY_EXISTS = "Korisničko ime ili e-mail već se koristi"

# Hash lozinke koja ne pripada nikome: provjera se izvodi i kad korisnik ne postoji,
# pa ni trajanje odgovora ne odaje postoji li korisničko ime
_DUMMY_HASH = hash_password("dummy-password-for-timing")


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    user = await user_repo.get_by_username(db, username)
    password_ok = verify_password(password, user.password_hash if user else _DUMMY_HASH)
    # Nepostojeći korisnik, kriva lozinka i deaktiviran račun: isti odgovor
    if not user or not password_ok or not user.is_active:
        raise AppError("invalid_credentials", INVALID_CREDENTIALS, 401)
    return user


async def register_user(db: AsyncSession, body: UserCreate) -> User:
    if (
        await user_repo.get_by_username(db, body.username)
        or await user_repo.get_by_email(db, str(body.email))
    ):
        raise AppError("account_already_exists", ACCOUNT_ALREADY_EXISTS, 409)

    user = User(
        username=body.username,
        email=str(body.email),
        password_hash=hash_password(body.password),
        role="user",
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError("account_already_exists", ACCOUNT_ALREADY_EXISTS, 409)
    await db.refresh(user)
    return user


def create_tokens(user: User) -> tuple[str, str]:
    return create_access_token(user.id, user.role), create_refresh_token(user.id)


async def get_user_from_token(db: AsyncSession, token: str, expected_type: str) -> User:
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except ExpiredSignatureError:
        raise AppError("token_expired", "Token je istekao", 401)
    except (InvalidTokenError, ValueError):
        raise AppError("invalid_credentials", "Neispravan token", 401)

    # Access i refresh token potpisani su istim ključem, pa vrsta mora biti provjerena
    if payload.get("type") != expected_type:
        raise AppError("invalid_credentials", "Neispravan token", 401)

    # Token opisuje stanje u trenutku izdavanja; račun je u međuvremenu
    # mogao biti deaktiviran, pa zapis čitamo iz baze
    user = await user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise AppError("invalid_credentials", "Neispravan token", 401)
    return user


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> tuple[str, str]:
    user = await get_user_from_token(db, refresh_token, "refresh")
    # Novi par: i refresh token dobiva novi vijek
    return create_tokens(user)