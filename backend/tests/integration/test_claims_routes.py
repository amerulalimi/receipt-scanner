import io
import zipfile
from decimal import Decimal
from unittest.mock import patch

import pytest

from tests.conftest import (
    register_and_login,
    seed_approved_receipt,
    seed_claim_summary,
    TestSessionLocal,
)


@pytest.mark.integration
async def test_claims_summary_requires_auth(receipt_client):
    response = await receipt_client.get("/api/v1/claims/summary")
    assert response.status_code == 401


@pytest.mark.integration
async def test_claims_summary_shape(receipt_client):
    await register_and_login(receipt_client, email="claims-summary@example.com")

    async with TestSessionLocal() as session:
        from app.repositories.user import UserRepository

        user_repo = UserRepository(session)
        user = await user_repo.get_by_email("claims-summary@example.com")
        assert user is not None
        await seed_claim_summary(
            session,
            user_id=user.id,
            tax_year=2025,
            category="perubatan",
            total_claimed=Decimal("1000.00"),
        )

    response = await receipt_client.get("/api/v1/claims/summary?tax_year=2025")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["tax_year"] == 2025
    assert isinstance(data["categories"], list)
    assert "limit_amount" in data["categories"][0] or "limit" in data["categories"][0]


@pytest.mark.integration
async def test_claims_compare_endpoint(receipt_client):
    await register_and_login(receipt_client, email="claims-compare@example.com")
    response = await receipt_client.get("/api/v1/claims/compare?tax_year=2025")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["current_year"] == 2025
    assert data["previous_year"] == 2024


@pytest.mark.integration
async def test_claims_completeness_endpoint(receipt_client):
    await register_and_login(receipt_client, email="claims-complete@example.com")
    response = await receipt_client.get("/api/v1/claims/completeness?tax_year=2025")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "score" in data
    assert "breakdown" in data
    assert "next_action" in data


@pytest.mark.integration
async def test_claims_ready_to_file_endpoint(receipt_client):
    await register_and_login(receipt_client, email="claims-ready@example.com")
    response = await receipt_client.get("/api/v1/claims/ready-to-file?tax_year=2025")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "filing_checklist" in data
    assert "total_relief" in data
    assert "fields" in data


@pytest.mark.integration
async def test_claims_export_zip(receipt_client):
    await register_and_login(receipt_client, email="claims-export@example.com")

    async with TestSessionLocal() as session:
        from app.repositories.user import UserRepository

        user_repo = UserRepository(session)
        user = await user_repo.get_by_email("claims-export@example.com")
        assert user is not None
        await seed_approved_receipt(
            session,
            user_id=user.id,
            category="perubatan",
            claimed_amount=Decimal("250.00"),
        )

    fake_content = b"fake-image"
    with patch("app.services.export.get_receipt_storage") as mock_storage_factory:
        mock_storage = mock_storage_factory.return_value
        mock_storage.read_receipt_file.return_value = fake_content

        response = await receipt_client.get("/api/v1/claims/export-zip?tax_year=2025")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "ResitCukai_BE_2025" in response.headers.get("content-disposition", "")

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert f"Ringkasan_Tuntutan_2025.txt" in archive.namelist()
