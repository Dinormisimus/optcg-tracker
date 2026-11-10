import asyncio
import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.deps import get_db
from app.main import create_app
from app.models import Base, Leader, Tournament, User


def _test_database_url() -> str:
    if test_url := os.environ.get("TEST_DATABASE_URL"):
        return test_url
    url = make_url(settings.DATABASE_URL)
    if not url.database:
        raise ValueError("DATABASE_URL must include a database name")
    if not url.database.endswith("_test"):
        url = url.set(database=f"{url.database}_test")
    return url.render_as_string(hide_password=False)


TEST_DATABASE_URL = _test_database_url()
engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


async def _prepare_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    if not url.database:
        raise ValueError("TEST_DATABASE_URL must include a database name")
    if url.database == make_url(settings.DATABASE_URL).database:
        raise ValueError("TEST_DATABASE_URL must not point to the development database")
    database_name = url.database.replace('"', '""')
    server = create_async_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        poolclass=NullPool,
    )
    try:
        async with server.connect() as connection:
            exists = await connection.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": url.database},
            )
            if not exists:
                await connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    finally:
        await server.dispose()

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    asyncio.run(_prepare_database())


@pytest.fixture(autouse=True)
async def clean_tables(test_database: None) -> None:
    table_names = ", ".join(f'"{table.name}"' for table in Base.metadata.sorted_tables)
    async with engine.begin() as connection:
        await connection.execute(
            text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE")
        )


async def _get_test_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    app.dependency_overrides[get_db] = _get_test_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


def _password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=4)).decode()


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    user = User(
        username="testadmin",
        email="admin@example.com",
        password_hash=_password_hash("admin123"),
        role="admin",
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def player_user(db: AsyncSession) -> User:
    user = User(
        username="testplayer",
        email="player@example.com",
        password_hash=_password_hash("player123"),
        role="user",
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def inactive_user(db: AsyncSession) -> User:
    user = User(
        username="inactive",
        email="inactive@example.com",
        password_hash=_password_hash("inactive123"),
        role="user",
        is_active=False,
    )
    db.add(user)
    await db.commit()
    return user


@pytest.fixture
async def leader(db: AsyncSession) -> Leader:
    leader = Leader(name="Test Leader", code="OP99-001", color="Red")
    db.add(leader)
    await db.commit()
    return leader


@pytest.fixture
async def tournament(db: AsyncSession, admin_user: User) -> Tournament:
    tournament = Tournament(name="Test Tournament", organizer_id=admin_user.id)
    db.add(tournament)
    await db.commit()
    return tournament


def expired_token(user_id: int) -> str:
    import jwt

    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "iss": settings.JWT_ISSUER,
            "exp": datetime(2000, 1, 1, tzinfo=UTC),
        },
        settings.JWT_SECRET,
        algorithm="HS256",
    )


async def auth_header(
    client: AsyncClient, username: str, password: str
) -> dict[str, str]:
    response = await client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
