import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.exceptions import AppError
from app.models.claim_summary import ClaimSummary
from app.models.spouse_link import SpouseLink
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.receipt import ReceiptRepository
from app.schemas.household import SpouseLinkRequest, SpouseLinkRespondRequest
from app.services.household import HouseholdService
from tests.conftest import seed_approved_receipt, seed_relief_limits, seed_user


@pytest.mark.asyncio
async def test_request_spouse_link_success(db_session, test_user):
    partner = await seed_user(db_session, email="spouse@example.com", full_name="Spouse")
    service = HouseholdService(db_session)

    link = await service.request_spouse_link(
        test_user,
        SpouseLinkRequest(partner_email=partner.email),
    )

    assert link.status == "pending"
    assert link.partner_email == partner.email.lower()
    assert link.requester_id == test_user.id


@pytest.mark.asyncio
async def test_request_spouse_link_already_linked(db_session, test_user):
    partner = await seed_user(db_session, email="spouse@example.com")
    service = HouseholdService(db_session)
    db_session.add(
        SpouseLink(
            id=uuid.uuid4(),
            requester_id=test_user.id,
            partner_id=partner.id,
            partner_email=partner.email,
            status="accepted",
            responded_at=datetime.now(UTC),
        ),
    )
    await db_session.commit()

    with pytest.raises(AppError) as exc_info:
        await service.request_spouse_link(
            test_user,
            SpouseLinkRequest(partner_email="other@example.com"),
        )
    assert exc_info.value.code == "ALREADY_LINKED"


@pytest.mark.asyncio
async def test_request_spouse_link_pending_exists(db_session, test_user):
    service = HouseholdService(db_session)
    db_session.add(
        SpouseLink(
            id=uuid.uuid4(),
            requester_id=test_user.id,
            partner_email="pending@example.com",
            status="pending",
        ),
    )
    await db_session.commit()

    with pytest.raises(AppError) as exc_info:
        await service.request_spouse_link(
            test_user,
            SpouseLinkRequest(partner_email="pending@example.com"),
        )
    assert exc_info.value.code == "REQUEST_PENDING"


@pytest.mark.asyncio
async def test_respond_accept(db_session):
    requester = await seed_user(db_session, email="requester@example.com")
    partner = await seed_user(db_session, email="partner@example.com")
    link = SpouseLink(
        id=uuid.uuid4(),
        requester_id=requester.id,
        partner_email=partner.email,
        status="pending",
    )
    db_session.add(link)
    await db_session.commit()

    service = HouseholdService(db_session)
    updated = await service.respond_to_link(
        partner,
        link.id,
        SpouseLinkRespondRequest(action="accept"),
    )

    assert updated.status == "accepted"
    assert updated.partner_id == partner.id
    assert updated.responded_at is not None


@pytest.mark.asyncio
async def test_respond_reject(db_session):
    requester = await seed_user(db_session, email="requester2@example.com")
    partner = await seed_user(db_session, email="partner2@example.com")
    link = SpouseLink(
        id=uuid.uuid4(),
        requester_id=requester.id,
        partner_email=partner.email,
        status="pending",
    )
    db_session.add(link)
    await db_session.commit()

    service = HouseholdService(db_session)
    updated = await service.respond_to_link(
        partner,
        link.id,
        SpouseLinkRespondRequest(action="reject"),
    )

    assert updated.status == "rejected"
    assert updated.responded_at is not None


@pytest.mark.asyncio
async def test_dissolve_link(db_session):
    requester = await seed_user(db_session, email="dissolve-a@example.com")
    partner = await seed_user(db_session, email="dissolve-b@example.com")
    link = SpouseLink(
        id=uuid.uuid4(),
        requester_id=requester.id,
        partner_id=partner.id,
        partner_email=partner.email,
        status="accepted",
        responded_at=datetime.now(UTC),
    )
    db_session.add(link)
    await db_session.commit()

    service = HouseholdService(db_session)
    await service.dissolve_link(requester, link.id)
    await db_session.refresh(link)

    assert link.status == "dissolved"


@pytest.mark.asyncio
async def test_reassign_receipt(db_session):
    await seed_relief_limits(db_session)
    user_a = await seed_user(db_session, email="reassign-a@example.com")
    user_b = await seed_user(db_session, email="reassign-b@example.com")
    db_session.add(
        SpouseLink(
            id=uuid.uuid4(),
            requester_id=user_a.id,
            partner_id=user_b.id,
            partner_email=user_b.email,
            status="accepted",
            responded_at=datetime.now(UTC),
        ),
    )
    receipt = await seed_approved_receipt(
        db_session,
        user_id=user_a.id,
        claimed_amount=Decimal("200.00"),
    )
    db_session.add(
        ClaimSummary(
            id=uuid.uuid4(),
            user_id=user_a.id,
            tax_year=2025,
            category="perubatan",
            total_claimed=Decimal("200.00"),
            receipt_count=1,
            last_updated=datetime.now(UTC),
        ),
    )
    await db_session.commit()

    service = HouseholdService(db_session)
    await service.reassign_receipt(
        user_a,
        receipt.id,
        target_user_id=user_b.id,
    )

    updated = await ReceiptRepository(db_session).get_by_id(receipt.id)
    assert updated is not None
    assert updated.user_id == user_b.id

    claims = ClaimSummaryRepository(db_session)
    source_summary = await claims.get(user_id=user_a.id, tax_year=2025, category="perubatan")
    target_summary = await claims.get(user_id=user_b.id, tax_year=2025, category="perubatan")
    assert source_summary is not None and source_summary.total_claimed == Decimal("0")
    assert target_summary is not None and target_summary.total_claimed == Decimal("200.00")


@pytest.mark.asyncio
async def test_claim_suggestion_no_spouse(db_session, test_user):
    receipt = await seed_approved_receipt(db_session, user_id=test_user.id)
    service = HouseholdService(db_session)

    result = await service.suggest_claim_owner(test_user, receipt.id)

    assert result.suggestion == "self"


@pytest.mark.asyncio
async def test_claim_suggestion_spouse_higher_bracket(db_session):
    await seed_relief_limits(db_session)
    user = await seed_user(
        db_session,
        email="bracket-user@example.com",
        tax_bracket=Decimal("11"),
    )
    spouse = await seed_user(
        db_session,
        email="bracket-spouse@example.com",
        tax_bracket=Decimal("24"),
    )
    db_session.add(
        SpouseLink(
            id=uuid.uuid4(),
            requester_id=user.id,
            partner_id=spouse.id,
            partner_email=spouse.email,
            status="accepted",
            responded_at=datetime.now(UTC),
        ),
    )
    receipt = await seed_approved_receipt(db_session, user_id=user.id)
    await db_session.commit()

    service = HouseholdService(db_session)
    result = await service.suggest_claim_owner(user, receipt.id)

    assert result.suggestion == "spouse"


@pytest.mark.asyncio
async def test_claim_suggestion_self_more_remaining(db_session):
    await seed_relief_limits(db_session)
    user = await seed_user(
        db_session,
        email="remaining-user@example.com",
        tax_bracket=Decimal("24"),
    )
    spouse = await seed_user(
        db_session,
        email="remaining-spouse@example.com",
        tax_bracket=Decimal("24"),
    )
    db_session.add(
        SpouseLink(
            id=uuid.uuid4(),
            requester_id=user.id,
            partner_id=spouse.id,
            partner_email=spouse.email,
            status="accepted",
            responded_at=datetime.now(UTC),
        ),
    )
    db_session.add(
        ClaimSummary(
            id=uuid.uuid4(),
            user_id=spouse.id,
            tax_year=2025,
            category="perubatan",
            total_claimed=Decimal("7000.00"),
            receipt_count=5,
            last_updated=datetime.now(UTC),
        ),
    )
    receipt = await seed_approved_receipt(db_session, user_id=user.id)
    await db_session.commit()

    service = HouseholdService(db_session)
    result = await service.suggest_claim_owner(user, receipt.id)

    assert result.suggestion == "self"
