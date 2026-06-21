from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.claims import CategoryClaimSummary, ClaimCompareData, ClaimSummaryData


class ClaimsService:
    WARNING_THRESHOLD = Decimal("0.90")

    def __init__(self, db: AsyncSession) -> None:
        self._claims = ClaimSummaryRepository(db)
        self._limits = ReliefLimitRepository(db)

    async def get_summary(
        self,
        user: User,
        *,
        tax_year: int | None = None,
    ) -> ClaimSummaryData:
        year = tax_year or user.tax_year
        limits = await self._limits.list_active()
        summaries = await self._claims.list_for_user(user_id=user.id, tax_year=year)
        summary_by_category = {summary.category: summary for summary in summaries}

        categories: list[CategoryClaimSummary] = []
        total_claimed = Decimal("0")

        for limit in limits:
            summary = summary_by_category.get(limit.category)
            claimed = summary.total_claimed if summary else Decimal("0")
            receipt_count = summary.receipt_count if summary else 0
            remaining = max(Decimal("0"), limit.limit_amount - claimed)
            percentage = float(
                (claimed / limit.limit_amount * 100).quantize(Decimal("0.1"))
                if limit.limit_amount > 0
                else Decimal("0"),
            )

            if claimed >= limit.limit_amount:
                status = "full"
            elif claimed >= limit.limit_amount * self.WARNING_THRESHOLD:
                status = "warning"
            else:
                status = "ok"

            categories.append(
                CategoryClaimSummary(
                    category=limit.category,
                    be_seksyen=limit.be_seksyen,
                    limit=limit.limit_amount,
                    claimed=claimed,
                    remaining=remaining,
                    percentage=percentage,
                    receipt_count=receipt_count,
                    status=status,
                ),
            )
            total_claimed += claimed

        tax_bracket = user.tax_bracket or Decimal("0")
        estimated_savings = (
            total_claimed * tax_bracket / Decimal("100")
        ).quantize(Decimal("0.01"))

        return ClaimSummaryData(
            tax_year=year,
            tax_bracket=float(tax_bracket),
            estimated_savings=estimated_savings,
            categories=categories,
        )

    async def get_comparison(
        self,
        user: User,
        *,
        tax_year: int | None = None,
    ) -> ClaimCompareData:
        year = tax_year or user.tax_year
        previous_year = year - 1

        current = await self.get_summary(user, tax_year=year)
        previous = await self.get_summary(user, tax_year=previous_year)

        return ClaimCompareData(
            current_year=year,
            previous_year=previous_year,
            current=current,
            previous=previous,
        )
