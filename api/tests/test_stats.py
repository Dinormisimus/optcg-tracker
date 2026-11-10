from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Leader, User
from tests.conftest import auth_header


async def _create_match(
    client: AsyncClient,
    headers: dict[str, str],
    my_leader_id: int,
    opponent_leader_id: int,
    opponent_name: str,
    result: str,
):
    return await client.post(
        "/matches",
        json={
            "my_leader_id": my_leader_id,
            "opponent_leader_id": opponent_leader_id,
            "opponent_name": opponent_name,
            "result": result,
            "dice_result": "WIN",
            "turn_order": "FIRST",
        },
        headers=headers,
    )


async def test_stats_calculate_overall_leader_opponent_and_matchup_rates(
    client: AsyncClient,
    db: AsyncSession,
    admin_user: User,
    leader: Leader,
):
    second_leader = Leader(name="Blue Leader", code="OP99-020", color="Blue")
    opponent_leader = Leader(name="Opponent Leader", code="OP99-021", color="Purple")
    second_opponent_leader = Leader(
        name="Second Opponent Leader", code="OP99-022", color="Green"
    )
    db.add_all([second_leader, opponent_leader, second_opponent_leader])
    await db.commit()
    headers = await auth_header(client, "testadmin", "admin123")

    responses = [
        await _create_match(
            client, headers, leader.id, opponent_leader.id, "Alice", "WIN"
        ),
        await _create_match(
            client, headers, leader.id, second_opponent_leader.id, "alice", "LOSS"
        ),
        await _create_match(
            client, headers, second_leader.id, opponent_leader.id, "Bob", "DRAW"
        ),
        await _create_match(
            client, headers, second_leader.id, opponent_leader.id, "Alice", "WIN"
        ),
    ]
    assert all(response.status_code == 201 for response in responses)

    overall = await client.get("/stats/overall", headers=headers)
    by_leader = await client.get("/stats/leaders", headers=headers)
    by_opponent = await client.get("/stats/opponents", headers=headers)
    by_opponent_leader = await client.get("/stats/opponent-leaders", headers=headers)
    matchups = await client.get("/stats/matchups", headers=headers)

    assert overall.status_code == 200
    assert overall.json() == {
        "total_matches": 4,
        "wins": 2,
        "losses": 1,
        "draws": 1,
        "decided_matches": 3,
        "win_rate": 66.67,
    }

    leader_stats = {item["leader_id"]: item for item in by_leader.json()}
    assert leader_stats[leader.id]["win_rate"] == 50.0
    assert leader_stats[second_leader.id]["win_rate"] == 100.0
    assert leader_stats[second_leader.id]["draws"] == 1

    opponent_stats = {
        item["opponent_name"].casefold(): item for item in by_opponent.json()
    }
    assert opponent_stats["alice"]["total_matches"] == 3
    assert opponent_stats["alice"]["win_rate"] == 66.67
    assert opponent_stats["bob"]["win_rate"] is None

    opponent_leader_stats = {
        item["opponent_leader_id"]: item for item in by_opponent_leader.json()
    }
    assert opponent_leader_stats[opponent_leader.id]["win_rate"] == 100.0
    assert opponent_leader_stats[second_opponent_leader.id]["win_rate"] == 0.0

    matchup_stats = {
        (item["opponent_name"].casefold(), item["opponent_leader_id"]): item
        for item in matchups.json()
    }
    assert matchup_stats[("alice", opponent_leader.id)]["wins"] == 2
    assert matchup_stats[("alice", second_opponent_leader.id)]["losses"] == 1


async def test_stats_are_private_and_group_lists_are_paginated(
    client: AsyncClient,
    admin_user: User,
    player_user: User,
    leader: Leader,
    db: AsyncSession,
):
    second_leader = Leader(name="Second Leader", code="OP99-030", color="Blue")
    third_leader = Leader(name="Third Leader", code="OP99-031", color="Green")
    db.add_all([second_leader, third_leader])
    await db.commit()

    admin_headers = await auth_header(client, "testadmin", "admin123")
    player_headers = await auth_header(client, "testplayer", "player123")
    await _create_match(
        client, admin_headers, leader.id, leader.id, "Opponent A", "WIN"
    )
    await _create_match(
        client, admin_headers, second_leader.id, leader.id, "Opponent B", "LOSS"
    )
    await _create_match(
        client, admin_headers, third_leader.id, leader.id, "Opponent C", "DRAW"
    )

    admin_stats = await client.get("/stats/overall", headers=admin_headers)
    player_stats = await client.get("/stats/overall", headers=player_headers)
    page = await client.get("/stats/leaders?limit=1&offset=1", headers=admin_headers)
    invalid_page = await client.get("/stats/opponents?limit=0", headers=admin_headers)

    assert admin_stats.json()["total_matches"] == 3
    assert player_stats.json()["total_matches"] == 0
    assert page.status_code == 200
    assert len(page.json()) == 1
    assert page.json()[0]["leader_id"] == second_leader.id
    assert invalid_page.status_code == 422


async def test_stats_require_authentication(client: AsyncClient):
    response = await client.get("/stats/overall")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"
