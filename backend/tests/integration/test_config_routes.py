import pytest
from datetime import UTC, datetime
from unittest.mock import patch

from tests.conftest import TestSessionLocal, register_and_login, seed_platform_admin
from app.schemas.openrouter_models import OpenRouterModelOption, OpenRouterModelsData
from app.services.openrouter_models import OpenRouterModelsResult


async def _login_platform_admin(
    client,
    *,
    email: str = "cfg-admin@example.com",
    password: str = "Senario@123",
) -> str:
    async with TestSessionLocal() as session:
        await seed_platform_admin(session, email=email, password=password)

    response = await client.post(
        "/api/v1/admin/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.headers.get("set-cookie", "").split(";")[0]


@pytest.mark.integration
async def test_get_relief_limits_superadmin(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-admin@example.com")
    response = await phase6_client.get(
        "/api/v1/config/relief-limits",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


@pytest.mark.integration
async def test_get_relief_limits_forbidden(phase6_client):
    await register_and_login(phase6_client, email="cfg-employee@example.com")
    response = await phase6_client.get("/api/v1/config/relief-limits")
    assert response.status_code == 401


@pytest.mark.integration
async def test_update_relief_limit(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-patch@example.com")
    response = await phase6_client.patch(
        "/api/v1/config/relief-limits/perubatan",
        json={"limit_amount": "8100.00"},
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    assert float(response.json()["data"]["limit_amount"]) == 8100.0


@pytest.mark.integration
async def test_get_system_overview(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-overview@example.com")
    response = await phase6_client.get(
        "/api/v1/config/system/overview",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "total_users" in data
    assert "redis_connected" in data


@pytest.mark.integration
async def test_purge_retention(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-purge@example.com")
    response = await phase6_client.post(
        "/api/v1/config/system/purge-retention",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "purged_receipts" in data or "receipts_deleted" in data


@pytest.mark.integration
async def test_get_settings(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-settings@example.com")
    response = await phase6_client.get(
        "/api/v1/config/settings",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200


@pytest.mark.integration
async def test_put_setting(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-put@example.com")
    response = await phase6_client.put(
        "/api/v1/config/settings/openrouter_vision_model",
        json={"value": "google/gemini-2.5-flash"},
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200


@pytest.mark.integration
async def test_get_secrets_masked(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-secrets@example.com")
    response = await phase6_client.get(
        "/api/v1/config/secrets",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    items = response.json()["data"]
    for item in items:
        if item.get("masked_value"):
            assert "•" in item["masked_value"]


@pytest.mark.integration
async def test_put_secret(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-secret-put@example.com")
    response = await phase6_client.put(
        "/api/v1/config/secrets/openrouter_api_key",
        json={"value": "sk-or-v1-test-key-long-enough"},
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200


@pytest.mark.integration
async def test_get_openrouter_models(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-models@example.com")
    mocked = OpenRouterModelsResult(
        data=OpenRouterModelsData(
            models=[
                OpenRouterModelOption(
                    id="google/gemini-2.5-flash",
                    name="Gemini 2.5 Flash",
                    prompt_price_per_million_usd=0.15,
                    completion_price_per_million_usd=0.6,
                    image_token_price_per_million_usd=0.0,
                )
            ],
            fetched_at=datetime.now(UTC),
            message=None,
        ),
    )

    with patch(
        "app.api.v1.routes.config_secrets.list_openrouter_vision_models",
        return_value=mocked,
    ):
        response = await phase6_client.get(
            "/api/v1/config/secrets/openrouter/models",
            headers={"Cookie": cookie},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert len(payload["data"]["models"]) == 1
    assert payload["data"]["models"][0]["id"] == "google/gemini-2.5-flash"
    assert payload["data"]["models"][0]["prompt_price_per_million_usd"] == 0.15


@pytest.mark.integration
async def test_get_audit_logs(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="cfg-audit@example.com")
    response = await phase6_client.get(
        "/api/v1/config/audit-logs?page=1&limit=50",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "items" in data
    assert data["limit"] == 50
