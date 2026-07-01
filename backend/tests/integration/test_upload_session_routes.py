import pytest

from tests.conftest import make_test_jpeg, register_and_login


@pytest.mark.integration
async def test_create_upload_session(receipt_client):
    await register_and_login(receipt_client, email="upload-session@example.com")
    response = await receipt_client.post(
        "/api/v1/upload-sessions",
        json={"tax_year": 2025},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token"]


@pytest.mark.integration
async def test_validate_token_valid(receipt_client):
    await register_and_login(receipt_client, email="validate@example.com")
    created = await receipt_client.post("/api/v1/upload-sessions", json={})
    token = created.json()["data"]["token"]

    response = await receipt_client.get(f"/api/v1/upload-sessions/{token}/validate")
    assert response.status_code == 200
    assert response.json()["data"]["valid"] is True


@pytest.mark.integration
async def test_validate_token_expired(receipt_client):
    await register_and_login(receipt_client, email="expired@example.com")
    created = await receipt_client.post("/api/v1/upload-sessions", json={})
    token = created.json()["data"]["token"]

    close_resp = await receipt_client.post(f"/api/v1/upload-sessions/{token}/close")
    assert close_resp.status_code == 200

    response = await receipt_client.get(f"/api/v1/upload-sessions/{token}/validate")
    assert response.status_code == 401


@pytest.mark.integration
async def test_mobile_upload(receipt_client):
    await register_and_login(receipt_client, email="mobile@example.com")
    created = await receipt_client.post("/api/v1/upload-sessions", json={})
    token = created.json()["data"]["token"]

    files = {"file": ("receipt.jpg", make_test_jpeg(), "image/jpeg")}
    response = await receipt_client.post(
        f"/api/v1/upload-sessions/{token}/upload",
        files=files,
        headers={"User-Agent": "MobileTest/1.0"},
    )
    assert response.status_code == 202
    assert response.json()["data"]["job_id"]


@pytest.mark.integration
async def test_keep_alive(receipt_client):
    await register_and_login(receipt_client, email="keepalive@example.com")
    created = await receipt_client.post("/api/v1/upload-sessions", json={})
    token = created.json()["data"]["token"]

    response = await receipt_client.post(
        f"/api/v1/upload-sessions/{token}/keep-alive",
        headers={"User-Agent": "MobileTest/1.0"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["inactivity_remaining"] > 0


@pytest.mark.integration
async def test_close_session(receipt_client):
    await register_and_login(receipt_client, email="close@example.com")
    created = await receipt_client.post("/api/v1/upload-sessions", json={})
    token = created.json()["data"]["token"]

    response = await receipt_client.post(f"/api/v1/upload-sessions/{token}/close")
    assert response.status_code == 200
    assert "uploads_count" in response.json()["data"]


@pytest.mark.integration
async def test_relief_categories_public(receipt_client):
    response = await receipt_client.get("/api/v1/config/relief-categories")
    assert response.status_code == 200
    categories = response.json()["data"]
    assert len(categories) == 7
