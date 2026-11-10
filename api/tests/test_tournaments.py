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
    registration = await client.post(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": leader.id},
        headers=headers,
    )
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

    assert registration.status_code == 201
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


async def test_user_can_join_tournament_and_see_own_participations(
    client: AsyncClient,
    player_user: User,
    tournament: Tournament,
    leader: Leader,
):
    headers = await auth_header(client, "testplayer", "player123")
    joined = await client.post(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": leader.id},
        headers=headers,
    )
    mine = await client.get("/tournaments/mine", headers=headers)
    roster = await client.get(
        f"/tournaments/{tournament.id}/participants", headers=headers
    )

    assert joined.status_code == 201
    assert joined.json()["user_id"] == player_user.id
    assert joined.json()["leader_id"] == leader.id
    assert mine.status_code == 200
    assert mine.json()[0]["tournament_id"] == tournament.id
    assert mine.json()[0]["leader_code"] == leader.code
    assert roster.status_code == 200
    assert roster.json()[0]["username"] == player_user.username


async def test_participant_can_change_leader_before_first_tournament_match(
    client: AsyncClient,
    player_user: User,
    tournament: Tournament,
    leader: Leader,
    db: AsyncSession,
):
    second_leader = Leader(name="Second Leader", code="OP99-010", color="Blue")
    db.add(second_leader)
    await db.commit()
    headers = await auth_header(client, "testplayer", "player123")
    joined = await client.post(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": leader.id},
        headers=headers,
    )

    changed = await client.patch(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": second_leader.id},
        headers=headers,
    )

    assert joined.status_code == 201
    assert changed.status_code == 200
    assert changed.json()["leader_id"] == second_leader.id


async def test_participant_leader_is_locked_after_first_tournament_match(
    client: AsyncClient,
    player_user: User,
    tournament: Tournament,
    leader: Leader,
    db: AsyncSession,
):
    second_leader = Leader(name="Second Leader", code="OP99-011", color="Blue")
    db.add(second_leader)
    await db.commit()
    player_headers = await auth_header(client, "testplayer", "player123")
    joined = await client.post(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": leader.id},
        headers=player_headers,
    )
    match = await client.post(
        "/matches",
        json={
            "my_leader_id": leader.id,
            "opponent_leader_id": leader.id,
            "opponent_name": "Guest",
            "result": "WIN",
            "dice_result": "WIN",
            "turn_order": "FIRST",
            "tournament_id": tournament.id,
        },
        headers=player_headers,
    )
    changed = await client.patch(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": second_leader.id},
        headers=player_headers,
    )
    unchanged = await client.patch(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": leader.id},
        headers=player_headers,
    )

    assert joined.status_code == 201
    assert match.status_code == 201
    assert changed.status_code == 409
    assert changed.json()["code"] == "leader_locked"
    assert unchanged.status_code == 200


async def test_tournament_match_requires_only_reporter_to_be_registered(
    client: AsyncClient,
    admin_user: User,
    player_user: User,
    tournament: Tournament,
    leader: Leader,
    db: AsyncSession,
):
    opponent_leader = Leader(name="Opponent Leader", code="OP99-012", color="Blue")
    db.add(opponent_leader)
    await db.commit()
    player_headers = await auth_header(client, "testplayer", "player123")
    player_join = await client.post(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": opponent_leader.id},
        headers=player_headers,
    )

    wrong_own_leader = await client.post(
        "/matches",
        json={
            "my_leader_id": leader.id,
            "opponent_leader_id": leader.id,
            "opponent_user_id": admin_user.id,
            "opponent_name": admin_user.username,
            "result": "WIN",
            "dice_result": "WIN",
            "turn_order": "FIRST",
            "tournament_id": tournament.id,
        },
        headers=player_headers,
    )
    wrong_opponent_leader = await client.post(
        "/matches",
        json={
            "my_leader_id": opponent_leader.id,
            "opponent_leader_id": opponent_leader.id,
            "opponent_user_id": admin_user.id,
            "opponent_name": admin_user.username,
            "result": "WIN",
            "dice_result": "WIN",
            "turn_order": "FIRST",
            "tournament_id": tournament.id,
        },
        headers=player_headers,
    )
    assert player_join.status_code == 201
    assert wrong_own_leader.status_code == 409
    assert wrong_own_leader.json()["code"] == "tournament_leader_mismatch"
    assert wrong_opponent_leader.status_code == 201
    assert wrong_opponent_leader.json()["opponent_user_id"] == admin_user.id


async def test_participant_cannot_leave_after_recording_match(
    client: AsyncClient,
    player_user: User,
    tournament: Tournament,
    leader: Leader,
):
    headers = await auth_header(client, "testplayer", "player123")
    joined = await client.post(
        f"/tournaments/{tournament.id}/participants/me",
        json={"leader_id": leader.id},
        headers=headers,
    )
    await client.post(
        "/matches",
        json={
            "my_leader_id": leader.id,
            "opponent_leader_id": leader.id,
            "opponent_name": "Guest",
            "result": "LOSS",
            "dice_result": "LOSS",
            "turn_order": "SECOND",
            "tournament_id": tournament.id,
        },
        headers=headers,
    )

    response = await client.delete(
        f"/tournaments/{tournament.id}/participants/me", headers=headers
    )

    assert joined.status_code == 201
    assert response.status_code == 409
    assert response.json()["code"] == "participation_has_matches"
