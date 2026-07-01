import uuid
from decimal import Decimal

import pytest

from app.services.borang_be import BorangBeService
from app.services.claims import ClaimsService
from app.services.engagement import EngagementService
from tests.conftest import seed_claim_summary, seed_relief_limits


@pytest.mark.asyncio
async def test_claim_summary_status_ok_warning_full(db_session, test_user):
    await seed_relief_limits(db_session)
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="perubatan",
        total_claimed=Decimal("4000.00"),
    )
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="gaya_hidup",
        total_claimed=Decimal("2400.00"),
    )
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="sukan",
        total_claimed=Decimal("500.00"),
    )

    test_user.tax_bracket = Decimal("13")
    service = ClaimsService(db_session)
    summary = await service.get_summary(test_user, tax_year=2025)

    by_category = {item.category: item for item in summary.categories}
    assert by_category["perubatan"].status == "ok"
    assert by_category["gaya_hidup"].status == "warning"
    assert by_category["sukan"].status == "full"
    assert summary.estimated_savings == Decimal("897.00")


@pytest.mark.asyncio
async def test_year_comparison(db_session, test_user):
    await seed_relief_limits(db_session)
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="perubatan",
        total_claimed=Decimal("1000.00"),
    )
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2024,
        category="perubatan",
        total_claimed=Decimal("500.00"),
    )

    service = ClaimsService(db_session)
    comparison = await service.get_comparison(test_user, tax_year=2025)

    assert comparison.current_year == 2025
    assert comparison.previous_year == 2024
    assert comparison.current.categories[0].total_claimed == Decimal("1000.00")
    assert comparison.previous.categories[0].total_claimed == Decimal("500.00")


@pytest.mark.asyncio
async def test_completeness_score_zero_and_full(db_session, test_user):
    await seed_relief_limits(db_session)
    engagement = EngagementService(db_session)

    empty_score = await engagement.get_completeness_score(test_user, tax_year=2025)
    assert empty_score.score == 0
    assert empty_score.next_action is not None
    assert len(empty_score.breakdown) == 5

    test_user.full_name = "QR Tester"
    test_user.tax_bracket = Decimal("13")
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="perubatan",
        total_claimed=Decimal("5000.00"),
    )
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="gaya_hidup",
        total_claimed=Decimal("1500.00"),
    )
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="pendidikan",
        total_claimed=Decimal("3500.00"),
    )

    from tests.conftest import seed_approved_receipt

    await seed_approved_receipt(
        db_session,
        user_id=test_user.id,
        category="perubatan",
        claimed_amount=Decimal("5000.00"),
    )

    full_score = await engagement.get_completeness_score(test_user, tax_year=2025)
    assert full_score.score == 100
    assert full_score.next_action is None


@pytest.mark.asyncio
async def test_ready_to_file_filing_checklist(db_session, test_user):
    await seed_relief_limits(db_session)
    await seed_claim_summary(
        db_session,
        user_id=test_user.id,
        tax_year=2025,
        category="perubatan",
        total_claimed=Decimal("1200.00"),
        receipt_count=2,
    )

    service = BorangBeService(db_session)
    data = await service.get_ready_to_file(test_user, tax_year=2025)

    assert data.total_relief == data.total_claimed
    assert len(data.filing_checklist) > 0
    perubatan = next(
        item for item in data.filing_checklist if item.amount_to_enter > 0
    )
    assert perubatan.status == "ready"
    assert perubatan.amount_to_enter == Decimal("1200.00")
    assert perubatan.receipt_count == 2
