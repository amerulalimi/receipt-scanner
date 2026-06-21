import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_summary import ClaimSummary
from app.models.receipt import Receipt


class ClaimSummaryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
    ) -> ClaimSummary | None:
        result = await self._db.execute(
            select(ClaimSummary).where(
                ClaimSummary.user_id == user_id,
                ClaimSummary.tax_year == tax_year,
                ClaimSummary.category == category,
            ),
        )
        return result.scalar_one_or_none()

    async def get_approved_total(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
    ) -> Decimal:
        summary = await self.get(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
        )
        if summary is None:
            return Decimal("0")
        return summary.total_claimed

    async def adjust(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        amount_delta: Decimal,
        count_delta: int,
    ) -> ClaimSummary:
        summary = await self.get(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
        )

        if summary is None:
            summary = ClaimSummary(
                user_id=user_id,
                tax_year=tax_year,
                category=category,
                total_claimed=max(Decimal("0"), amount_delta),
                receipt_count=max(0, count_delta),
            )
            self._db.add(summary)
        else:
            summary.total_claimed = max(Decimal("0"), summary.total_claimed + amount_delta)
            summary.receipt_count = max(0, summary.receipt_count + count_delta)
            summary.last_updated = datetime.now(UTC)

        await self._db.flush()
        await self._db.refresh(summary)
        return summary

    async def sum_pending_claimed(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        exclude_receipt_id: uuid.UUID | None = None,
    ) -> Decimal:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.category == category,
            Receipt.deleted_at.is_(None),
            Receipt.status.in_(("pending", "flagged")),
        ]
        if exclude_receipt_id is not None:
            conditions.append(Receipt.id != exclude_receipt_id)

        result = await self._db.execute(
            select(func.coalesce(func.sum(Receipt.claimed_amount), 0)).where(*conditions),
        )
        total = result.scalar_one()
        return Decimal(str(total))

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
    ) -> list[ClaimSummary]:
        result = await self._db.execute(
            select(ClaimSummary)
            .where(
                ClaimSummary.user_id == user_id,
                ClaimSummary.tax_year == tax_year,
            )
            .order_by(ClaimSummary.category),
        )
        return list(result.scalars().all())
