from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import UserInSession
from app.models.user import User
from app.repositories.claim_summary import ClaimSummaryRepository
from app.schemas.claims import CategoryClaimSummary, ClaimCompareData, ClaimSummaryData


class ClaimsService:
    def __init__(self, db: AsyncSession) -> None:
        self._claims = ClaimSummaryRepository(db)

    async def get_summary(
        self,
        user: User,
        session: UserInSession | None = None,
        *,
        tax_year: int | None = None,
    ) -> ClaimSummaryData:
        year = tax_year or user.tax_year
        active_context = session.active_context if session is not None else "individual"
        active_org_id = (
            session.org_id if session is not None and session.active_context == "corporate" else None
        )
        rows = await self._claims.get_summary(
            user_id=user.id,
            tax_year=year,
            context_type=active_context,
            org_id=active_org_id,
        )

        categories: list[CategoryClaimSummary] = []
        total_claimed = Decimal("0")

        for row in rows:
            categories.append(
                CategoryClaimSummary(
                    category=row["category"],
                    be_seksyen=row["be_seksyen"],
                    limit_amount=row["limit_amount"],
                    total_claimed=row["total_claimed"],
                    remaining=row["remaining"],
                    percentage=row["percentage"],
                    receipt_count=row["receipt_count"],
                    status=row["status"],
                    limit=row["limit_amount"],
                    claimed=row["total_claimed"],
                ),
            )
            total_claimed += row["total_claimed"]

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
        session: UserInSession | None = None,
        *,
        tax_year: int | None = None,
    ) -> ClaimCompareData:
        year = tax_year or user.tax_year
        previous_year = year - 1

        current = await self.get_summary(user, session, tax_year=year)
        previous = await self.get_summary(user, session, tax_year=previous_year)

        return ClaimCompareData(
            current_year=year,
            previous_year=previous_year,
            current=current,
            previous=previous,
        )
