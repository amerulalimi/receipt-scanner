import pytest


@pytest.mark.integration
async def test_health_returns_200(async_client) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200


@pytest.mark.integration
async def test_health_response_body(async_client) -> None:
    response = await async_client.get("/health")
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] in {"ok", "degraded", "down"}
    assert body["data"]["version"] == "1.1.0"
    assert "checks" in body["data"]


@pytest.mark.integration
async def test_health_cors_header(async_client) -> None:
    response = await async_client.get(
        "/health",
        headers={"Origin": "http://localhost:3000"},
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
