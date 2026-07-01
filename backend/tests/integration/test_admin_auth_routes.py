import pytest

ADMIN_LOGIN_PAYLOAD = {
    "email": "admin@admin.com",
    "password": "Senario@123",
}


@pytest.mark.integration
async def test_admin_login_success(admin_auth_client, seeded_platform_admin):
    response = await admin_auth_client.post(
        "/api/v1/admin/auth/login",
        json=ADMIN_LOGIN_PAYLOAD,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == ADMIN_LOGIN_PAYLOAD["email"]
    assert "resit_admin_sess" in response.headers.get("set-cookie", "")


@pytest.mark.integration
async def test_admin_login_wrong_password(admin_auth_client, seeded_platform_admin):
    response = await admin_auth_client.post(
        "/api/v1/admin/auth/login",
        json={
            "email": ADMIN_LOGIN_PAYLOAD["email"],
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.integration
async def test_admin_get_me_authenticated(admin_auth_client, seeded_platform_admin):
    login = await admin_auth_client.post(
        "/api/v1/admin/auth/login",
        json=ADMIN_LOGIN_PAYLOAD,
    )
    cookie = login.headers.get("set-cookie", "").split(";")[0]
    response = await admin_auth_client.get(
        "/api/v1/admin/auth/me",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == ADMIN_LOGIN_PAYLOAD["email"]


@pytest.mark.integration
async def test_admin_get_me_unauthenticated(admin_auth_client):
    response = await admin_auth_client.get("/api/v1/admin/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
async def test_admin_logout(admin_auth_client, seeded_platform_admin):
    login = await admin_auth_client.post(
        "/api/v1/admin/auth/login",
        json=ADMIN_LOGIN_PAYLOAD,
    )
    cookie = login.headers.get("set-cookie", "").split(";")[0]
    response = await admin_auth_client.post(
        "/api/v1/admin/auth/logout",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    me = await admin_auth_client.get(
        "/api/v1/admin/auth/me",
        headers={"Cookie": cookie},
    )
    assert me.status_code == 401


@pytest.mark.integration
async def test_admin_refresh(admin_auth_client, seeded_platform_admin):
    login = await admin_auth_client.post(
        "/api/v1/admin/auth/login",
        json=ADMIN_LOGIN_PAYLOAD,
    )
    cookie = login.headers.get("set-cookie", "").split(";")[0]
    response = await admin_auth_client.post(
        "/api/v1/admin/auth/refresh",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    assert "resit_admin_sess" in response.headers.get("set-cookie", "")
