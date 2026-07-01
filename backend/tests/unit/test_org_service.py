from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import AppError
from app.repositories.organisation import OrganisationRepository
from app.repositories.user import UserRepository
from app.schemas.org import OrgPolicyUpdateRequest, OrgRegisterRequest
from app.services.export import ExportService
from app.services.org import OrgService
from app.services.org_analytics import OrgAnalyticsService
from tests.conftest import seed_approved_receipt, seed_organisation, seed_relief_limits


@pytest.mark.asyncio
async def test_register_org_success(db_session, test_user):
    test_user.account_type = "corporate"
    test_user.role = "individual"
    test_user.email = "founder@example.com"
    await db_session.commit()

    service = OrgService(db_session)
    with patch("app.services.org.AuditService.log", new_callable=AsyncMock):
        result = await service.register_org(
            test_user,
            OrgRegisterRequest(
                name="Acme Sdn Bhd",
                ssm_number="111222-A",
                email_domain="example.com",
            ),
        )

    assert result.name == "Acme Sdn Bhd"
    await db_session.refresh(test_user)
    assert test_user.role == "superadmin"
    assert test_user.org_id is not None


@pytest.mark.asyncio
async def test_register_org_duplicate_ssm(db_session, test_user):
    test_user.account_type = "corporate"
    test_user.email = "founder@example.com"
    await db_session.commit()
    await seed_organisation(db_session, superadmin_email="other@example.com", ssm_number="DUP-SSM")

    service = OrgService(db_session)
    with pytest.raises(AppError) as exc_info:
        await service.register_org(
            test_user,
            OrgRegisterRequest(
                name="Other Co",
                ssm_number="DUP-SSM",
                email_domain="example.com",
            ),
        )
    assert exc_info.value.code == "ORG_SSM_EXISTS"


@pytest.mark.asyncio
async def test_register_org_duplicate_domain(db_session, test_user):
    test_user.account_type = "corporate"
    test_user.email = "founder@taken.example.com"
    await db_session.commit()
    await seed_organisation(db_session, email_domain="taken.example.com")

    service = OrgService(db_session)
    with pytest.raises(AppError) as exc_info:
        await service.register_org(
            test_user,
            OrgRegisterRequest(
                name="New Co",
                ssm_number="999888-A",
                email_domain="taken.example.com",
            ),
        )
    assert exc_info.value.code == "ORG_DOMAIN_EXISTS"


@pytest.mark.asyncio
async def test_update_policy(db_session):
    org, user = await seed_organisation(db_session)
    service = OrgService(db_session)
    await seed_relief_limits(db_session)

    with patch("app.services.org.AuditService.log", new_callable=AsyncMock):
        updated = await service.update_policy(
            user,
            OrgPolicyUpdateRequest(
                allowed_categories=["perubatan", "pendidikan"],
                require_hr_approval=False,
                max_receipts_per_month=25,
            ),
        )

    assert updated.require_hr_approval is False
    assert updated.max_receipts_per_month == 25
    assert "perubatan" in updated.allowed_categories


@pytest.mark.asyncio
async def test_get_analytics(db_session):
    org, admin = await seed_organisation(db_session)
    await seed_relief_limits(db_session)
    user_repo = UserRepository(db_session)
    employee = await user_repo.create(
        email="emp@example.com",
        password_hash="hashed",
        full_name="Employee One",
        role="employee",
        org_id=org.id,
        account_type="corporate",
    )
    receipt = await seed_approved_receipt(
        db_session,
        user_id=employee.id,
        category="perubatan",
        claimed_amount=Decimal("300.00"),
    )
    receipt.org_id = org.id
    await db_session.commit()

    analytics_service = OrgAnalyticsService(db_session)
    top_employees = await analytics_service._top_employees(org.id, 2025)
    assert top_employees


@pytest.mark.asyncio
async def test_export_payroll_csv(db_session):
    org, admin = await seed_organisation(db_session)
    await seed_relief_limits(db_session)
    user_repo = UserRepository(db_session)
    employee = await user_repo.create(
        email="payroll@example.com",
        password_hash="hashed",
        full_name="Payroll Emp",
        role="employee",
        org_id=org.id,
        account_type="corporate",
        org_employee_code="E001",
    )
    receipt = await seed_approved_receipt(
        db_session,
        user_id=employee.id,
        category="perubatan",
        claimed_amount=Decimal("150.00"),
    )
    receipt.org_id = org.id
    await db_session.commit()

    service = ExportService(db_session)
    content, filename = await service.build_org_payroll_csv(org.id, tax_year=2025)
    assert "employee_id" in content
    assert "E001" in content
    assert filename.startswith("Syarikat")
    assert filename.endswith("_payroll.csv")
