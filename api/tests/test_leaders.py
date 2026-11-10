from httpx import AsyncClient

from app.models import User
from tests.conftest import auth_header


async def test_leader_list_supports_limit_and_offset(
    client: AsyncClient, admin_user: User
):
    headers = await auth_header(client, "testadmin", "admin123")
    for code in ("OP99-001", "OP99-002", "OP99-003"):
        response = await client.post(
            "/leaders",
            json={"name": f"Leader {code}", "code": code, "color": "Red"},
            headers=headers,
        )
        assert response.status_code == 201

    page = await client.get("/leaders?limit=1&offset=1")

    assert page.status_code == 200
    assert len(page.json()) == 1
    assert page.json()[0]["code"] == "OP99-002"


async def test_leader_list_rejects_invalid_pagination(client: AsyncClient):
    zero_limit = await client.get("/leaders?limit=0")
    excessive_limit = await client.get("/leaders?limit=101")
    negative_offset = await client.get("/leaders?offset=-1")

    assert zero_limit.status_code == 422
    assert excessive_limit.status_code == 422
    assert negative_offset.status_code == 422
