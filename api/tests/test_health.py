from httpx import AsyncClient


async def test_health_returns_database_version(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"].startswith("PostgreSQL")
