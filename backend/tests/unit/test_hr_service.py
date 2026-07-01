from datetime import UTC, datetime
from decimal import Decimal
import uuid

import pytest

from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.user import UserRepository
from app.schemas.receipt import ReceiptReviewRequest
from app.services.receipt import ReceiptService
from tests.conftest import seed_organisation, seed_relief_limits


@pytest.mark.asyncio
async def test_review_receipt_approve_updates_summary(db_session):
    org, hr = await seed_organisation(db_session)
    await seed_relief_limits(db_session)
    hr.role = "hr_admin"
    await db_session.commit()

    user_repo = UserRepository(db_session)
    employee = await user_repo.create(
        email="worker@example.com",
        password_hash="hashed",
        full_name="Worker",
        role="employee",
        org_id=org.id,
        account_type="corporate",
    )

    from app.models.receipt import Receipt

    receipt = Receipt(
        id=uuid.uuid4(),
        user_id=employee.id,
        org_id=org.id,
        tax_year=2025,
        image_key="test/pending.jpg",
        image_hash="hash-pending-1",
        merchant_name="Clinic",
        category="perubatan",
        claimed_amount=Decimal("200.00"),
        status="pending",
        scan_status="success",
    )
    db_session.add(receipt)
    await db_session.commit()
    await db_session.refresh(receipt)

    service = ReceiptService(db_session)
    updated = await service.review_receipt(
        hr,
        receipt.id,
        ReceiptReviewRequest(action="approve"),
    )
    assert updated.status == "approved"

    summary = await ClaimSummaryRepository(db_session).get(
        user_id=employee.id,
        tax_year=2025,
        category="perubatan",
    )
    assert summary is not None
    assert summary.total_claimed == Decimal("200.00")


@pytest.mark.asyncio
async def test_review_receipt_reject_no_summary(db_session):
    org, hr = await seed_organisation(db_session)
    await seed_relief_limits(db_session)
    hr.role = "hr_admin"
    await db_session.commit()

    user_repo = UserRepository(db_session)
    employee = await user_repo.create(
        email="reject@example.com",
        password_hash="hashed",
        full_name="Reject Me",
        role="employee",
        org_id=org.id,
        account_type="corporate",
    )

    from app.models.receipt import Receipt

    receipt = Receipt(
        id=uuid.uuid4(),
        user_id=employee.id,
        org_id=org.id,
        tax_year=2025,
        image_key="test/reject.jpg",
        image_hash="hash-reject-1",
        category="perubatan",
        claimed_amount=Decimal("100.00"),
        status="pending",
        scan_status="success",
    )
    db_session.add(receipt)
    await db_session.commit()

    service = ReceiptService(db_session)
    updated = await service.review_receipt(
        hr,
        receipt.id,
        ReceiptReviewRequest(action="reject", comment="Not valid"),
    )
    assert updated.status == "rejected"

    summary = await ClaimSummaryRepository(db_session).get(
        user_id=employee.id,
        tax_year=2025,
        category="perubatan",
    )
    assert summary is None


@pytest.mark.asyncio
async def test_bulk_approve_counts(db_session):
    org, hr = await seed_organisation(db_session)
    await seed_relief_limits(db_session)
    hr.role = "hr_admin"
    await db_session.commit()

    user_repo = UserRepository(db_session)
    employee = await user_repo.create(
        email="bulk@example.com",
        password_hash="hashed",
        full_name="Bulk Worker",
        role="employee",
        org_id=org.id,
        account_type="corporate",
    )

    from app.models.receipt import Receipt

    for index in range(2):
        db_session.add(
            Receipt(
                id=uuid.uuid4(),
                user_id=employee.id,
                org_id=org.id,
                tax_year=2025,
                image_key=f"test/bulk-{index}.jpg",
                image_hash=f"hash-bulk-{index}",
                category="perubatan",
                claimed_amount=Decimal("50.00"),
                status="pending",
                scan_status="success",
            ),
        )
    await db_session.commit()

    service = ReceiptService(db_session)
    approved, skipped = await service.bulk_approve_org_pending(hr, tax_year=2025)
    assert approved == 2
    assert skipped == 0
