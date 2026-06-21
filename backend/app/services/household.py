from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.spouse_link import SpouseLink
from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.spouse_link import SpouseLinkRepository
from app.repositories.user import UserRepository
from app.schemas.household import (
    ClaimSuggestionData,
    HouseholdCategorySummary,
    HouseholdCombinedSummary,
    HouseholdMemberSummary,
    HouseholdOverviewData,
    SpouseIncomingRequest,
    SpouseLinkRequest,
    SpouseLinkRespondRequest,
    SpouseOutgoingRequest,
)
from app.services.claim_limit import NON_CLAIMABLE_CATEGORIES


class HouseholdService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._links = SpouseLinkRepository(db)
        self._users = UserRepository(db)
        self._claims = ClaimSummaryRepository(db)
        self._receipts = ReceiptRepository(db)

    async def get_overview(self, user: User) -> HouseholdOverviewData:
        accepted = await self._links.get_accepted_for_user(user.id)
        incoming = await self._links.get_pending_for_email(user.email.lower())
        outgoing = await self._links.get_pending_outgoing(user.id)

        partner = None
        combined = None
        if accepted is not None:
            partner_id = (
                accepted.partner_id
                if accepted.requester_id == user.id
                else accepted.requester_id
            )
            if partner_id is not None:
                partner_user = await self._users.get_by_id(partner_id)
                if partner_user is not None:
                    partner = await self._member_summary(partner_user)
                    combined = await self._combined_summary(user, partner_user)

        return HouseholdOverviewData(
            accepted_link_id=accepted.id if accepted else None,
            partner=partner,
            combined=combined,
            incoming_requests=[
                SpouseIncomingRequest(
                    id=link.id,
                    requester_name=link.requester.full_name if link.requester else None,
                    requester_email=link.requester.email if link.requester else "",
                    created_at=link.created_at,
                )
                for link in incoming
            ],
            outgoing_request=(
                SpouseOutgoingRequest(
                    id=outgoing.id,
                    partner_email=outgoing.partner_email,
                    created_at=outgoing.created_at,
                )
                if outgoing
                else None
            ),
        )

    async def request_spouse_link(
        self,
        user: User,
        payload: SpouseLinkRequest,
    ) -> SpouseLink:
        if user.account_type != "individual":
            raise AppError(
                message="Pautan pasangan hanya untuk akaun individu.",
                code="FORBIDDEN",
                status_code=403,
            )

        partner_email = payload.partner_email.strip().lower()
        if partner_email == user.email.lower():
            raise AppError(
                message="Tidak boleh pautkan dengan diri sendiri.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        existing = await self._links.get_accepted_for_user(user.id)
        if existing is not None:
            raise AppError(
                message="Anda sudah mempunyai pasangan dipautkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        pending = await self._links.get_pending_outgoing(user.id)
        if pending is not None:
            raise AppError(
                message="Permintaan pautan pasangan masih menunggu.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        partner = await self._users.get_by_email(partner_email)
        if partner is not None:
            partner_existing = await self._links.get_accepted_for_user(partner.id)
            if partner_existing is not None:
                raise AppError(
                    message="Pasangan sudah dipautkan dengan akaun lain.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )

        link = SpouseLink(
            requester_id=user.id,
            partner_id=partner.id if partner else None,
            partner_email=partner_email,
            status="pending",
        )
        return await self._links.create(link)

    async def respond_to_link(
        self,
        user: User,
        link_id: uuid.UUID,
        payload: SpouseLinkRespondRequest,
    ) -> SpouseLink:
        link = await self._links.get_by_id(link_id)
        if link is None or link.status != "pending":
            raise AppError(
                message="Permintaan pautan tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if link.partner_email.lower() != user.email.lower():
            raise AppError(
                message="Akses ditolak.",
                code="FORBIDDEN",
                status_code=403,
            )

        if payload.action == "accept":
            existing = await self._links.get_accepted_for_user(user.id)
            if existing is not None:
                raise AppError(
                    message="Anda sudah mempunyai pasangan dipautkan.",
                    code="VALIDATION_ERROR",
                    status_code=422,
                )
            link.mark_responded(status="accepted", partner_id=user.id)
        else:
            link.mark_responded(status="rejected", partner_id=user.id)

        await self._db.flush()
        await self._db.refresh(link)
        return link

    async def dissolve_link(self, user: User, link_id: uuid.UUID) -> None:
        link = await self._links.get_by_id(link_id)
        if link is None or link.status != "accepted":
            raise AppError(
                message="Pautan pasangan tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if user.id not in {link.requester_id, link.partner_id}:
            raise AppError(
                message="Akses ditolak.",
                code="FORBIDDEN",
                status_code=403,
            )

        link.status = "dissolved"
        link.responded_at = link.responded_at
        await self._db.flush()

    async def reassign_receipt(
        self,
        user: User,
        receipt_id: uuid.UUID,
        *,
        target_user_id: uuid.UUID,
    ) -> None:
        link = await self._links.get_accepted_for_user(user.id)
        if link is None:
            raise AppError(
                message="Pautkan pasangan dahulu.",
                code="FORBIDDEN",
                status_code=403,
            )

        spouse_id = (
            link.partner_id if link.requester_id == user.id else link.requester_id
        )
        if spouse_id is None or target_user_id not in {user.id, spouse_id}:
            raise AppError(
                message="Hanya boleh pindahkan antara pasangan dipautkan.",
                code="FORBIDDEN",
                status_code=403,
            )

        receipt = await self._receipts.get_by_id_for_user(receipt_id, user.id)
        if receipt is None:
            raise AppError(
                message="Resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if receipt.status == "approved":
            raise AppError(
                message="Resit diluluskan tidak boleh dipindahkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        receipt.user_id = target_user_id
        await self._db.flush()

    async def suggest_claim_owner(
        self,
        user: User,
        receipt_id: uuid.UUID,
    ) -> ClaimSuggestionData:
        link = await self._links.get_accepted_for_user(user.id)
        if link is None or link.partner_id is None:
            raise AppError(
                message="Pautkan pasangan dahulu.",
                code="FORBIDDEN",
                status_code=403,
            )

        spouse_id = (
            link.partner_id if link.requester_id == user.id else link.requester_id
        )
        if spouse_id is None:
            raise AppError(
                message="Pasangan tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        receipt = await self._receipts.get_by_id_for_user(receipt_id, user.id)
        if receipt is None:
            receipt = await self._receipts.get_by_id_for_user(receipt_id, spouse_id)
        if receipt is None or not receipt.category:
            raise AppError(
                message="Resit tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        spouse = await self._users.get_by_id(spouse_id)
        if spouse is None:
            raise AppError(
                message="Pasangan tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        user_remaining = await self._remaining_for_category(
            user,
            receipt.category,
            receipt.tax_year,
        )
        spouse_remaining = await self._remaining_for_category(
            spouse,
            receipt.category,
            receipt.tax_year,
        )
        user_bracket = float(user.tax_bracket or Decimal("0"))
        spouse_bracket = float(spouse.tax_bracket or Decimal("0"))

        suggested_user_id = user.id
        reason_my = "Anda mempunyai lebih baki had untuk kategori ini."
        reason_en = "You have more remaining limit in this category."

        if spouse_remaining > user_remaining:
            suggested_user_id = spouse.id
            reason_my = "Pasangan mempunyai lebih baki had untuk kategori ini."
            reason_en = "Your spouse has more remaining limit in this category."
        elif spouse_remaining == user_remaining and spouse_bracket > user_bracket:
            suggested_user_id = spouse.id
            reason_my = "Pasangan dalam bracket cukai lebih tinggi — nilai pelepasan lebih besar."
            reason_en = "Your spouse is in a higher tax bracket — relief value is larger."

        return ClaimSuggestionData(
            receipt_id=receipt.id,
            category=receipt.category,
            suggested_user_id=suggested_user_id,
            reason_my=reason_my,
            reason_en=reason_en,
            user_remaining=user_remaining,
            spouse_remaining=spouse_remaining,
        )

    async def _member_summary(self, user: User) -> HouseholdMemberSummary:
        summaries = await self._claims.list_for_user(
            user_id=user.id,
            tax_year=user.tax_year,
        )
        total = sum((item.total_claimed for item in summaries), Decimal("0"))
        return HouseholdMemberSummary(
            user_id=user.id,
            full_name=user.full_name,
            email=user.email,
            tax_year=user.tax_year,
            tax_bracket=float(user.tax_bracket or Decimal("0")),
            total_claimed=total,
            categories=[
                HouseholdCategorySummary(
                    category=item.category,
                    claimed=item.total_claimed,
                    receipt_count=item.receipt_count,
                )
                for item in summaries
            ],
        )

    async def _combined_summary(
        self,
        user: User,
        partner: User,
    ) -> HouseholdCombinedSummary:
        user_summary = await self._member_summary(user)
        partner_summary = await self._member_summary(partner)
        combined_total = user_summary.total_claimed + partner_summary.total_claimed
        return HouseholdCombinedSummary(
            tax_year=user.tax_year,
            combined_total_claimed=combined_total,
            members=[user_summary, partner_summary],
        )

    async def _remaining_for_category(
        self,
        user: User,
        category: str,
        tax_year: int,
    ) -> Decimal:
        if category in NON_CLAIMABLE_CATEGORIES:
            return Decimal("0")

        from app.services.claim_limit import ClaimLimitService

        check = await ClaimLimitService(self._db).check_claim(
            user_id=user.id,
            tax_year=tax_year,
            category=category,
            new_claimed_amount=Decimal("0"),
            raise_on_exceed=False,
        )
        return check.relief_status.remaining
