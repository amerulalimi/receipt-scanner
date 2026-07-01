import pytest

from tests.conftest import TestSessionLocal, register_and_login, seed_platform_admin


async def _login_platform_admin(
    client,
    *,
    email: str = "dir-admin@example.com",
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
async def test_list_admin_users_requires_auth(phase6_client):
    response = await phase6_client.get("/api/v1/admin/users")
    assert response.status_code == 401


@pytest.mark.integration
async def test_list_admin_users(phase6_client):
    cookie = await _login_platform_admin(phase6_client)
    response = await phase6_client.get(
        "/api/v1/admin/users?limit=50",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["limit"] == 50
    assert "items" in data
    assert "total" in data


@pytest.mark.integration
async def test_admin_user_stats(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="dir-stats@example.com")
    response = await phase6_client.get(
        "/api/v1/admin/users/stats?granularity=month",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert "series" in data
    assert "growth_percent" in data


@pytest.mark.integration
async def test_deactivate_admin_user(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="dir-del@example.com")
    await register_and_login(phase6_client, email="dir-target@example.com")

    list_response = await phase6_client.get(
        "/api/v1/admin/users?search=dir-target@example.com",
        headers={"Cookie": cookie},
    )
    user_id = list_response.json()["data"]["items"][0]["id"]

    delete_response = await phase6_client.delete(
        f"/api/v1/admin/users/{user_id}",
        headers={"Cookie": cookie},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["is_active"] is False


@pytest.mark.integration
async def test_list_admin_organizations(phase6_client):
    cookie = await _login_platform_admin(phase6_client, email="dir-orgs@example.com")
    response = await phase6_client.get(
        "/api/v1/admin/organizations?limit=50",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["limit"] == 50
    assert "items" in data
