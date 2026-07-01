from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import UserInSession
from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.claims import CompletenessBreakdownItem, CompletenessScoreData

CRITERION_APPROVED_RECEIPT = "approved_receipt"
CRITERION_MULTI_CATEGORY = "multi_category"
CRITERION_TOTAL_CLAIMED = "total_claimed_1000"
CRITERION_CATEGORY_UTILIZATION = "category_utilization_50"
CRITERION_PROFILE_COMPLETE = "profile_complete"

NEXT_ACTIONS = {
    CRITERION_APPROVED_RECEIPT: "Muat naik dan luluskan resit pertama anda.",
    CRITERION_MULTI_CATEGORY: "Tambah resit dalam sekurang-kurangnya 3 kategori pelepasan.",
    CRITERION_TOTAL_CLAIMED: "Tuntut lebih RM1,000 untuk markah penuh.",
    CRITERION_CATEGORY_UTILIZATION: "Gunakan sekurang-kurangnya 50% had pelepasan dalam satu kategori.",
    CRITERION_PROFILE_COMPLETE: "Lengkapkan profil anda (nama penuh dan kadar cukai).",
}

MILESTONE_MESSAGES = {
    0: "Mulakan dengan muat naik resit pertama anda.",
    20: "Permulaan yang baik — teruskan menjejak resit anda.",
    40: "Setengah jalan — tambah lebih banyak kategori pelepasan.",
    60: "Bagus! Anda sudah menuntut lebih RM1,000 tahun ini.",
    80: "Hampir lengkap — semak kategori yang masih rendah.",
    100: "Tahniah! Rekod tuntutan anda lengkap untuk tahun ini.",
}


class EngagementService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)
        self._receipts = ReceiptRepository(db)

    async def get_completeness_score(
        self,
        user: User,
        session: UserInSession | None = None,
        *,
        tax_year: int | None = None,
    ) -> CompletenessScoreData:
        year = tax_year or user.tax_year
        active_context = session.active_context if session is not None else "individual"
        active_org_id = (
            session.org_id if session is not None and session.active_context == "corporate" else None
        )
        summaries = await self._claims.list_for_user(
            user_id=user.id,
            tax_year=year,
            context_type=active_context,
            org_id=active_org_id,
        )
        summary_rows = await self._claims.get_summary(
            user_id=user.id,
            tax_year=year,
            context_type=active_context,
            org_id=active_org_id,
        )

        approved_count = await self._count_approved_receipts(user.id, active_org_id, year)
        categories_with_claims = sum(1 for item in summaries if item.receipt_count > 0)
        total_claimed = sum((item.total_claimed for item in summaries), Decimal("0"))

        has_category_half_used = any(
            row["limit_amount"] > 0 and row["total_claimed"] >= row["limit_amount"] * Decimal("0.50")
            for row in summary_rows
        )
        profile_complete = bool(user.full_name and user.full_name.strip()) and user.tax_bracket is not None

        breakdown: list[CompletenessBreakdownItem] = [
            CompletenessBreakdownItem(
                criterion=CRITERION_APPROVED_RECEIPT,
                achieved=approved_count >= 1,
                points=20 if approved_count >= 1 else 0,
            ),
            CompletenessBreakdownItem(
                criterion=CRITERION_MULTI_CATEGORY,
                achieved=categories_with_claims >= 3,
                points=20 if categories_with_claims >= 3 else 0,
            ),
            CompletenessBreakdownItem(
                criterion=CRITERION_TOTAL_CLAIMED,
                achieved=total_claimed > Decimal("1000"),
                points=20 if total_claimed > Decimal("1000") else 0,
            ),
            CompletenessBreakdownItem(
                criterion=CRITERION_CATEGORY_UTILIZATION,
                achieved=has_category_half_used,
                points=20 if has_category_half_used else 0,
            ),
            CompletenessBreakdownItem(
                criterion=CRITERION_PROFILE_COMPLETE,
                achieved=profile_complete,
                points=20 if profile_complete else 0,
            ),
        ]

        score = sum(item.points for item in breakdown)
        next_action = None
        for item in breakdown:
            if not item.achieved:
                next_action = NEXT_ACTIONS[item.criterion]
                break

        milestone_message = MILESTONE_MESSAGES.get(
            score - (score % 20),
            MILESTONE_MESSAGES[0],
        )

        tax_bracket = user.tax_bracket or Decimal("0")
        estimated_savings = (total_claimed * tax_bracket / Decimal("100")).quantize(Decimal("0.01"))

        limits = await self._limits.list_active()
        return CompletenessScoreData(
            tax_year=year,
            score=score,
            tracked_categories=categories_with_claims,
            total_categories=len(limits),
            categories_with_claims=categories_with_claims,
            total_claimed=total_claimed,
            estimated_savings=estimated_savings,
            milestone_message=milestone_message,
            next_action=next_action,
            breakdown=breakdown,
        )

    async def _count_approved_receipts(
        self,
        user_id,
        org_id,
        tax_year: int,
    ) -> int:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.deleted_at.is_(None),
            Receipt.status == "approved",
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        result = await self._db.execute(
            select(func.count()).select_from(Receipt).where(*conditions),
        )
        return int(result.scalar_one())
