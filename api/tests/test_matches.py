from httpx import AsyncClient

from app.models import Leader, Tournament, User
from tests.conftest import auth_header


def match_body(leader: Leader, **overrides) -> dict:
    body = {
        "my_leader_id": leader.id,
        "opponent_leader_id": leader.id,
        "opponent_name": "Opponent",
        "result": "WIN",
        "dice_result": "WIN",
        "turn_order": "FIRST",
    }
    return body | overrides


async def test_create_and_list_matches(
    client: AsyncClient, admin_user: User, leader: Leader
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.post("/matches", json=match_body(leader), headers=headers)

    assert response.status_code == 201
    created = response.json()
    assert created["user_id"] == admin_user.id
    assert created["my_leader_id"] == leader.id
    assert created["result"] == "WIN"
    assert "played_at" in created

    listed = await client.get("/matches?limit=1&offset=0", headers=headers)
    assert listed.status_code == 200
    assert [match["id"] for match in listed.json()] == [created["id"]]


async def test_match_list_is_private_and_paginated(
    client: AsyncClient,
    admin_user: User,
    player_user: User,
    leader: Leader,
):
    admin_headers = await auth_header(client, "testadmin", "admin123")
    player_headers = await auth_header(client, "testplayer", "player123")
    first = await client.post(
        "/matches", json=match_body(leader), headers=admin_headers
    )
    second = await client.post(
        "/matches",
        json=match_body(leader, result="LOSS"),
        headers=admin_headers,
    )

    page = await client.get("/matches?limit=1&offset=1", headers=admin_headers)
    player_list = await client.get("/matches", headers=player_headers)

    assert first.status_code == second.status_code == 201
    assert len(page.json()) == 1
    assert page.json()[0]["id"] != second.json()["id"]
    assert player_list.status_code == 200
    assert player_list.json() == []


async def test_user_cannot_read_update_or_delete_another_users_match(
    client: AsyncClient,
    admin_user: User,
    player_user: User,
    leader: Leader,
):
    admin_headers = await auth_header(client, "testadmin", "admin123")
    player_headers = await auth_header(client, "testplayer", "player123")
    created = await client.post(
        "/matches", json=match_body(leader), headers=admin_headers
    )
    match_id = created.json()["id"]

    get_response = await client.get(f"/matches/{match_id}", headers=player_headers)
    update_response = await client.patch(
        f"/matches/{match_id}", json={"result": "LOSS"}, headers=player_headers
    )
    delete_response = await client.delete(
        f"/matches/{match_id}", headers=player_headers
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert get_response.json()["code"] == "not_found"


async def test_owner_can_update_and_delete_match(
    client: AsyncClient, admin_user: User, leader: Leader
):
    headers = await auth_header(client, "testadmin", "admin123")
    created = await client.post("/matches", json=match_body(leader), headers=headers)
    match_id = created.json()["id"]

    updated = await client.patch(
        f"/matches/{match_id}", json={"result": "DRAW"}, headers=headers
    )
    deleted = await client.delete(f"/matches/{match_id}", headers=headers)
    missing = await client.get(f"/matches/{match_id}", headers=headers)

    assert updated.status_code == 200
    assert updated.json()["result"] == "DRAW"
    assert deleted.status_code == 204
    assert missing.status_code == 404


async def test_matches_require_authentication(client: AsyncClient, leader: Leader):
    response = await client.post("/matches", json=match_body(leader))

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_match_rejects_nonexistent_leader(client: AsyncClient, admin_user: User):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.post(
        "/matches",
        json={
            "my_leader_id": 999,
            "opponent_leader_id": 999,
            "opponent_name": "Opponent",
            "result": "WIN",
            "dice_result": "WIN",
            "turn_order": "FIRST",
        },
        headers=headers,
    )

    assert response.status_code == 404
    assert response.json()["code"] == "leader_not_found"


async def test_tournament_match_requires_a_round(
    client: AsyncClient,
    admin_user: User,
    leader: Leader,
    tournament: Tournament,
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.post(
        "/matches",
        json=match_body(leader, tournament_id=tournament.id),
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "tournament_round_required"


async def test_match_rejects_self_as_opponent(
    client: AsyncClient, admin_user: User, leader: Leader
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.post(
        "/matches",
        json=match_body(leader, opponent_user_id=admin_user.id),
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_opponent"


async def test_patch_cannot_set_required_fields_to_null(
    client: AsyncClient, admin_user: User, leader: Leader
):
    headers = await auth_header(client, "testadmin", "admin123")
    created = await client.post("/matches", json=match_body(leader), headers=headers)
    response = await client.patch(
        f"/matches/{created.json()['id']}",
        json={"result": None},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_match"


async def test_tournament_match_can_be_created_with_round(
    client: AsyncClient,
    admin_user: User,
    leader: Leader,
    tournament: Tournament,
):
    headers = await auth_header(client, "testadmin", "admin123")
    response = await client.post(
        "/matches",
        json=match_body(leader, tournament_id=tournament.id, round_number=1),
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["tournament_id"] == tournament.id
    assert response.json()["round_number"] == 1
