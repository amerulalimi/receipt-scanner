import io

import pytest
from PIL import Image

from tests.conftest import make_test_jpeg, register_and_login

REGISTER_PAYLOAD = {
    "email": "phase1@example.com",
    "password": "password123",
    "full_name": "Phase One",
    "account_type": "individual",
}


@pytest.mark.integration
async def test_security_headers_present(receipt_client):
    response = await receipt_client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "camera=()" in response.headers.get("Permissions-Policy", "")
    assert response.headers.get("Content-Security-Policy") == "default-src 'self'"


@pytest.mark.integration
async def test_x_request_id_present(receipt_client):
    response = await receipt_client.get("/health")
    assert response.headers.get("X-Request-ID")


@pytest.mark.integration
async def test_health_check_comprehensive(receipt_client):
    response = await receipt_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["status"] in {"ok", "degraded", "down"}
    assert data["version"] == "1.1.0"
    assert "environment" in data
    checks = data["checks"]
    assert checks["database"] in {"ok", "error"}
    assert checks["redis"] in {"ok", "error"}
    assert checks["storage"] in {"ok", "error"}
    assert checks["worker"] in {"running", "stopped"}


@pytest.mark.integration
async def test_rate_limit_login(auth_client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "auth_rate_limit_max", 5)

    email = "security-ratelimit@example.com"
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
    body = response.json()
    assert body["code"] == "RATE_LIMITED"
    assert body["message"] == "Terlalu banyak permintaan. Cuba lagi sebentar."


@pytest.mark.integration
async def test_file_magic_bytes_rejected(receipt_client):
    await register_and_login(receipt_client, email="magic-bytes@example.com")

    image = Image.new("RGB", (8, 8), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    png_bytes = buffer.getvalue()

    files = [("files", ("fake.jpg", png_bytes, "image/jpeg"))]
    response = await receipt_client.post("/api/v1/receipts/upload", files=files)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
