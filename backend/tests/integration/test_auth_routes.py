import pytest

REGISTER_PAYLOAD = {
    "email": "phase1@example.com",
    "password": "password123",
    "full_name": "Phase One",
    "account_type": "individual",
}


@pytest.mark.integration
async def test_register_endpoint(auth_client):
    response = await auth_client.post(
        "/api/v1/auth/register",
        json=REGISTER_PAYLOAD,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == REGISTER_PAYLOAD["email"]
    assert "resit_sess" in response.headers.get("set-cookie", "")


@pytest.mark.integration
async def test_register_duplicate(auth_client):
    await auth_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await auth_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 400
    assert response.json()["code"] == "EMAIL_EXISTS"


@pytest.mark.integration
async def test_login_success(auth_client):
    await auth_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "resit_sess" in response.headers.get("set-cookie", "")


@pytest.mark.integration
async def test_login_wrong_password(auth_client):
    await auth_client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    response = await auth_client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


@pytest.mark.integration
async def test_login_rate_limit(auth_client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "auth_rate_limit_max", 5)

    email = "ratelimit@example.com"
    await auth_client.post(
        "/api/v1/auth/register",
        json={**REGISTER_PAYLOAD, "email": email},
    )

    for _ in range(5):
        await auth_client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "wrong"},
        )

    response = await auth_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "wrong"},
    )
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMITED"


@pytest.mark.integration
async def test_get_me_authenticated(auth_client):
    reg = await auth_client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "email": "me@example.com",
    })
    cookie = reg.headers.get("set-cookie", "")
    response = await auth_client.get(
        "/api/v1/auth/me",
        headers={"Cookie": cookie.split(";")[0]},
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "me@example.com"


@pytest.mark.integration
async def test_get_me_unauthenticated(auth_client):
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.integration
async def test_logout(auth_client):
    reg = await auth_client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "email": "logout@example.com",
    })
    cookie_header = reg.headers.get("set-cookie", "")
    cookie = cookie_header.split(";")[0]
    response = await auth_client.post(
        "/api/v1/auth/logout",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    me = await auth_client.get("/api/v1/auth/me", headers={"Cookie": cookie})
    assert me.status_code == 401


@pytest.mark.integration
async def test_refresh(auth_client):
    reg = await auth_client.post("/api/v1/auth/register", json={
        **REGISTER_PAYLOAD,
        "email": "refresh@example.com",
    })
    cookie = reg.headers.get("set-cookie", "").split(";")[0]
    response = await auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": cookie},
    )
    assert response.status_code == 200
    assert response.json()["success"] is True
