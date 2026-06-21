from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.receipt import ReceiptRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.claims import CompletenessScoreData


class EngagementService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)
        self._receipts = ReceiptRepository(db)

    async def get_completeness_score(
        self,
        user: User,
        *,
        tax_year: int | None = None,
    ) -> CompletenessScoreData:
        year = tax_year or user.tax_year
        limits = await self._limits.list_active()
        summaries = await self._claims.list_for_user(user_id=user.id, tax_year=year)
        summary_by_category = {item.category: item for item in summaries}
        receipt_counts = await self._receipts.count_by_category_for_user_year(
            user_id=user.id,
            tax_year=year,
        )

        tracked_categories = 0
        total_categories = len(limits)
        total_utilization = Decimal("0")
        categories_with_claims = 0

        for limit in limits:
            summary = summary_by_category.get(limit.category)
            claimed = summary.total_claimed if summary else Decimal("0")
            limit_amount = Decimal(str(limit.limit_amount))
            if receipt_counts.get(limit.category, 0) > 0:
                tracked_categories += 1
            if claimed > 0:
                categories_with_claims += 1
            if limit_amount > 0:
                total_utilization += min(Decimal("1"), claimed / limit_amount)

        score = 0
        if total_categories > 0:
            tracking_pct = tracked_categories / total_categories
            utilization_pct = float(total_utilization / total_categories)
            score = int(round((tracking_pct * 0.5 + utilization_pct * 0.5) * 100))

        milestone = None
        total_claimed = sum(
            (item.total_claimed for item in summaries),
            Decimal("0"),
        )
        savings_estimate = total_claimed * (user.tax_bracket or Decimal("0")) / Decimal("100")
        if savings_estimate >= Decimal("1000"):
            milestone = "RM1,000+ estimated savings this year"

        return CompletenessScoreData(
            tax_year=year,
            score=min(100, max(0, score)),
            tracked_categories=tracked_categories,
            total_categories=total_categories,
            categories_with_claims=categories_with_claims,
            total_claimed=total_claimed,
            estimated_savings=savings_estimate.quantize(Decimal("0.01")),
            milestone_message=milestone,
        )
