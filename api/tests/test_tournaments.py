from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Leader, Tournament, User
from tests.conftest import auth_header


async def test_admin_can_create_and_list_tournaments(
    client: AsyncClient, admin_user: User
):
    headers = await auth_header(client, "testadmin", "admin123")
    created = await client.post(
        "/tournaments",
        json={"name": "Zadar Locals", "format": "SWISS"},
        headers=headers,
    )

    assert created.status_code == 201
    assert created.json()["name"] == "Zadar Locals"
    assert created.json()["format"] == "SWISS"
    assert created.json()["organizer_id"] == admin_user.id

    listed = await client.get("/tournaments?limit=10&offset=0", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]


async def test_regular_user_can_view_but_not_create_tournaments(
    client: AsyncClient, player_user: User, tournament: Tournament
):
    headers = await auth_header(client, "testplayer", "player123")

    listed = await client.get("/tournaments", headers=headers)
    detail = await client.get(f"/tournaments/{tournament.id}", headers=headers)
    created = await client.post(
        "/tournaments", json={"name": "Unauthorized"}, headers=headers
    )

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert detail.status_code == 200
    assert detail.json()["id"] == tournament.id
    assert created.status_code == 403
    assert created.json()["code"] == "forbidden"


async def test_tournament_list_supports_pagination_and_validates_parameters(
    client: AsyncClient, admin_user: User
):
    headers = await auth_header(client, "testadmin", "admin123")
    for name in ("Cup 1", "Cup 2", "Cup 3"):
        response = await client.post(
            "/tournaments", json={"name": name}, headers=headers
        )
        assert response.status_code == 201

    page = await client.get("/tournaments?limit=1&offset=1", headers=headers)
    invalid = await client.get("/tournaments?limit=0", headers=headers)

    assert page.status_code == 200
    assert len(page.json()) == 1
    assert page.json()[0]["name"] == "Cup 2"
    assert invalid.status_code == 422


async def test_only_organizer_or_super_admin_can_update_tournament(
    client: AsyncClient,
    db: AsyncSession,
    admin_user: User,
    super_admin_user: User,
    tournament: Tournament,
):
    other_admin = User(
        username="otheradmin",
        email="otheradmin@example.com",
        password_hash=admin_user.password_hash,
        role="admin",
    )
    db.add(other_admin)
    await db.commit()

    owner_headers = await auth_header(client, "testadmin", "admin123")
    other_admin_headers = await auth_header(client, "otheradmin", "admin123")
    super_admin_headers = await auth_header(client, "testsuperadmin", "superadmin123")

    updated = await client.patch(
        f"/tournaments/{tournament.id}",
        json={"name": "Updated Cup", "format": "CUSTOM"},
        headers=owner_headers,
    )
    forbidden = await client.patch(
        f"/tournaments/{tournament.id}",
        json={"name": "Not Allowed"},
        headers=other_admin_headers,
    )
    elevated = await client.patch(
        f"/tournaments/{tournament.id}",
        json={"name": "Super Admin Update"},
        headers=super_admin_headers,
    )

    assert updated.status_code == 200
    assert updated.json()["format"] == "CUSTOM"
    assert forbidden.status_code == 403
    assert elevated.status_code == 200


async def test_tournament_patch_rejects_null_values(
    client: AsyncClient, admin_user: User, tournament: Tournament
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.patch(
        f"/tournaments/{tournament.id}", json={"name": None}, headers=headers
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_tournament"


async def test_tournament_cannot_be_deleted_while_matches_reference_it(
    client: AsyncClient,
    admin_user: User,
    leader: Leader,
    tournament: Tournament,
):
    headers = await auth_header(client, "testadmin", "admin123")
    match = await client.post(
        "/matches",
        json={
            "my_leader_id": leader.id,
            "opponent_leader_id": leader.id,
            "opponent_name": "Opponent",
            "result": "WIN",
            "dice_result": "WIN",
            "turn_order": "FIRST",
            "tournament_id": tournament.id,
        },
        headers=headers,
    )

    response = await client.delete(f"/tournaments/{tournament.id}", headers=headers)

    assert match.status_code == 201
    assert response.status_code == 409
    assert response.json()["code"] == "tournament_has_matches"


async def test_organizer_can_delete_empty_tournament(
    client: AsyncClient, admin_user: User, tournament: Tournament
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.delete(f"/tournaments/{tournament.id}", headers=headers)
    missing = await client.get(f"/tournaments/{tournament.id}", headers=headers)

    assert response.status_code == 204
    assert missing.status_code == 404


async def test_tournament_endpoints_require_login(
    client: AsyncClient, tournament: Tournament
):
    response = await client.get(f"/tournaments/{tournament.id}")
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_missing_tournament_returns_not_found(
    client: AsyncClient, admin_user: User
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.get("/tournaments/999", headers=headers)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
