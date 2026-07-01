import pytest

from tests.conftest import TestSessionLocal, register_and_login


async def _promote_to_superadmin(email: str) -> None:
    from app.repositories.user import UserRepository

    async with TestSessionLocal() as session:
        user = await UserRepository(session).get_by_email(email)
        assert user is not None
        user.role = "superadmin"
        await session.commit()


@pytest.mark.integration
async def test_get_notifications(phase6_client):
    await register_and_login(phase6_client, email="notif-user@example.com")
    response = await phase6_client.get("/api/v1/notifications")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "items" in data


@pytest.mark.integration
async def test_dismiss(phase6_client):
    await register_and_login(phase6_client, email="notif-dismiss@example.com")
    listed = await phase6_client.get("/api/v1/notifications")
    items = listed.json()["data"]["items"]
    if not items:
        pytest.skip("No notifications generated in test environment")

    notification_id = items[0]["id"]
    response = await phase6_client.post(
        f"/api/v1/notifications/{notification_id}/dismiss",
    )
    assert response.status_code == 200


@pytest.mark.integration
async def test_get_preferences(phase6_client):
    await register_and_login(phase6_client, email="notif-prefs@example.com")
    response = await phase6_client.get("/api/v1/notifications/preferences")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["email_enabled"] is True


@pytest.mark.integration
async def test_update_preferences(phase6_client):
    await register_and_login(phase6_client, email="notif-prefs-upd@example.com")
    response = await phase6_client.patch(
        "/api/v1/notifications/preferences",
        json={"email_enabled": False},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email_enabled"] is False
