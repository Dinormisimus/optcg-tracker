from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from tests.conftest import auth_header, expired_token


async def login(client: AsyncClient, username: str, password: str):
    return await client.post(
        "/auth/login", json={"username": username, "password": password}
    )


async def test_register_creates_regular_user_with_hashed_password(
    client: AsyncClient, db: AsyncSession
):
    response = await client.post(
        "/auth/register",
        json={
            "username": "  newplayer  ",
            "email": "NewPlayer@example.com",
            "password": "secure-password",
            "role": "super_admin",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "newplayer"
    assert body["email"] == "newplayer@example.com"
    assert body["role"] == "user"
    assert body["is_active"] is True
    assert "password_hash" not in body

    user = await db.get(User, body["id"])
    assert user is not None
    assert user.password_hash != "secure-password"
    login_response = await login(client, "newplayer", "secure-password")
    assert login_response.status_code == 200


async def test_register_rejects_duplicate_username_or_email(
    client: AsyncClient, player_user: User
):
    duplicate_username = await client.post(
        "/auth/register",
        json={
            "username": "testplayer",
            "email": "different@example.com",
            "password": "secure-password",
        },
    )
    duplicate_email = await client.post(
        "/auth/register",
        json={
            "username": "different",
            "email": "player@example.com",
            "password": "secure-password",
        },
    )

    assert duplicate_username.status_code == 409
    assert duplicate_username.json()["code"] == "account_already_exists"
    assert duplicate_email.status_code == 409
    assert duplicate_email.json() == duplicate_username.json()


async def test_register_validates_password_and_email(client: AsyncClient):
    short_password = await client.post(
        "/auth/register",
        json={
            "username": "newplayer",
            "email": "newplayer@example.com",
            "password": "short",
        },
    )
    long_password = await client.post(
        "/auth/register",
        json={
            "username": "newplayer",
            "email": "newplayer@example.com",
            "password": "č" * 40,
        },
    )
    invalid_email = await client.post(
        "/auth/register",
        json={
            "username": "newplayer",
            "email": "not-an-email",
            "password": "secure-password",
        },
    )

    assert short_password.status_code == 422
    assert long_password.status_code == 422
    assert invalid_email.status_code == 422


async def test_login_returns_access_and_refresh_tokens(
    client: AsyncClient, admin_user: User
):
    response = await login(client, "testadmin", "admin123")

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_rejects_wrong_password_and_unknown_user(
    client: AsyncClient, admin_user: User
):
    wrong_password = await login(client, "testadmin", "wrong")
    unknown_user = await login(client, "missing", "wrong")

    assert wrong_password.status_code == 401
    assert wrong_password.json()["code"] == "invalid_credentials"
    assert unknown_user.status_code == 401
    assert unknown_user.json() == wrong_password.json()


async def test_login_rejects_inactive_user(client: AsyncClient, inactive_user: User):
    response = await login(client, "inactive", "inactive123")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_login_rejects_password_over_bcrypt_limit(
    client: AsyncClient, admin_user: User
):
    response = await login(client, "testadmin", "č" * 40)

    assert response.status_code == 422
    assert response.json()["code"] == "validation_error"


async def test_me_returns_user_without_password_hash(
    client: AsyncClient, player_user: User
):
    headers = await auth_header(client, "testplayer", "player123")
    response = await client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["username"] == "testplayer"
    assert response.json()["role"] == "user"
    assert "password_hash" not in response.json()


async def test_me_requires_a_valid_access_token(client: AsyncClient, admin_user: User):
    no_token = await client.get("/auth/me")
    assert no_token.status_code == 401
    assert no_token.json()["code"] == "invalid_credentials"

    tokens = (await login(client, "testadmin", "admin123")).json()
    refresh_as_access = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert refresh_as_access.status_code == 401

    invalid_token = ".".join(tokens["access_token"].split(".")[:2] + ["invalid"])
    invalid_signature = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {invalid_token}"}
    )
    assert invalid_signature.status_code == 401
    assert invalid_signature.json()["code"] == "invalid_credentials"

    expired = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {expired_token(admin_user.id)}"},
    )
    assert expired.status_code == 401
    assert expired.json()["code"] == "token_expired"


async def test_me_rejects_user_deactivated_after_login(
    client: AsyncClient, db: AsyncSession, admin_user: User
):
    headers = await auth_header(client, "testadmin", "admin123")
    await db.execute(
        update(User).where(User.id == admin_user.id).values(is_active=False)
    )
    await db.commit()

    response = await client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_refresh_returns_a_new_working_token_pair(
    client: AsyncClient, admin_user: User
):
    tokens = (await login(client, "testadmin", "admin123")).json()
    response = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )

    assert response.status_code == 200
    new_tokens = response.json()
    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
    me = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert me.status_code == 200


async def test_refresh_rejects_access_and_malformed_tokens(
    client: AsyncClient, admin_user: User
):
    tokens = (await login(client, "testadmin", "admin123")).json()
    access_token = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    malformed = await client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})

    assert access_token.status_code == 401
    assert malformed.status_code == 401
    assert access_token.json()["code"] == "invalid_credentials"
    assert malformed.json()["code"] == "invalid_credentials"


async def test_admin_role_protects_leader_creation(
    client: AsyncClient, admin_user: User, player_user: User
):
    body = {"name": "New Leader", "code": "OP99-002", "color": "Blue"}
    admin_headers = await auth_header(client, "testadmin", "admin123")
    player_headers = await auth_header(client, "testplayer", "player123")

    allowed = await client.post("/leaders", json=body, headers=admin_headers)
    denied = await client.post("/leaders", json=body, headers=player_headers)

    assert allowed.status_code == 201
    assert denied.status_code == 403
    assert denied.json()["code"] == "forbidden"
