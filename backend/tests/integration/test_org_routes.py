import uuid
from decimal import Decimal

import pytest

from tests.conftest import TestSessionLocal, setup_org_via_api


@pytest.mark.integration
async def test_org_register_requires_corporate_account(org_client):
    await org_client.post(
        "/api/v1/auth/register",
        json={
            "email": "indiv@example.com",
            "password": "password123",
            "full_name": "Individual",
            "account_type": "individual",
        },
    )
    response = await org_client.post(
        "/api/v1/org/register",
        json={
            "name": "Test Co",
            "ssm_number": "111111-A",
            "email_domain": "example.com",
        },
    )
    assert response.status_code == 403


@pytest.mark.integration
async def test_org_register_and_me(org_client):
    await setup_org_via_api(org_client, email="founder@example.com")

    response = await org_client.get("/api/v1/org/me")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Acme Sdn Bhd"
    assert data["email_domain"] == "example.com"


@pytest.mark.integration
async def test_org_policy_update_superadmin_only(org_client):
    await setup_org_via_api(org_client, email="admin@example.com")

    response = await org_client.patch(
        "/api/v1/org/policy",
        json={
            "allowed_categories": ["perubatan"],
            "require_hr_approval": True,
            "max_receipts_per_month": 10,
        },
    )
    assert response.status_code == 200
    policy = response.json()["data"]
    assert policy["max_receipts_per_month"] == 10


@pytest.mark.integration
async def test_org_employees_list(org_client):
    await setup_org_via_api(org_client, email="hr@example.com")

    response = await org_client.get("/api/v1/org/employees")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    assert any(item["email"] == "hr@example.com" for item in data["items"])


@pytest.mark.integration
async def test_org_pending_receipts_and_bulk_approve(org_client):
    await setup_org_via_api(org_client, email="super@example.com")

    async with TestSessionLocal() as session:
        from app.repositories.user import UserRepository
        from app.models.receipt import Receipt

        user_repo = UserRepository(session)
        org_admin = await user_repo.get_by_email("super@example.com")
        assert org_admin is not None

        employee = await user_repo.create(
            email="pending@example.com",
            password_hash="hashed",
            full_name="Pending Emp",
            role="employee",
            org_id=org_admin.org_id,
            account_type="corporate",
        )
        session.add(
            Receipt(
                id=uuid.uuid4(),
                user_id=employee.id,
                org_id=org_admin.org_id,
                tax_year=2025,
                image_key="test/pending-route.jpg",
                image_hash="hash-route-pending",
                category="perubatan",
                claimed_amount=Decimal("80.00"),
                status="pending",
                scan_status="success",
            ),
        )
        await session.commit()

    pending = await org_client.get("/api/v1/org/pending-receipts?tax_year=2025")
    assert pending.status_code == 200
    items = pending.json()["data"]["items"]
    assert len(items) >= 1

    bulk = await org_client.post("/api/v1/org/pending-receipts/bulk-approve?tax_year=2025")
    assert bulk.status_code == 200
    assert bulk.json()["data"]["approved_count"] >= 1


@pytest.mark.integration
async def test_org_analytics(org_client):
    await setup_org_via_api(org_client, email="analytics@example.com")

    response = await org_client.get("/api/v1/org/analytics?tax_year=2025")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "top_employees" in data
    assert "category_trend" in data


@pytest.mark.integration
async def test_org_export_csv_content_type(org_client):
    await setup_org_via_api(org_client, email="export@example.com")

    async with TestSessionLocal() as session:
        from app.models.receipt import Receipt
        from app.repositories.user import UserRepository

        user_repo = UserRepository(session)
        org_admin = await user_repo.get_by_email("export@example.com")
        assert org_admin is not None
        employee = await user_repo.create(
            email="payroll-emp@example.com",
            password_hash="hashed",
            full_name="Payroll Emp",
            role="employee",
            org_id=org_admin.org_id,
            account_type="corporate",
            org_employee_code="P001",
        )
        session.add(
            Receipt(
                id=uuid.uuid4(),
                user_id=employee.id,
                org_id=org_admin.org_id,
                tax_year=2025,
                image_key="test/export.jpg",
                image_hash="hash-export-1",
                category="perubatan",
                claimed_amount=Decimal("120.00"),
                status="approved",
                scan_status="success",
            ),
        )
        await session.commit()

    response = await org_client.get("/api/v1/org/export/csv?tax_year=2025")
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")
    disposition = response.headers.get("content-disposition", "")
    assert "Syarikat" in disposition
    assert "_payroll.csv" in disposition


@pytest.mark.integration
async def test_org_routes_forbidden_for_individual(org_client):
    await org_client.post(
        "/api/v1/auth/register",
        json={
            "email": "plain@example.com",
            "password": "password123",
            "full_name": "Plain User",
            "account_type": "individual",
        },
    )
    response = await org_client.get("/api/v1/org/employees")
    assert response.status_code == 403
