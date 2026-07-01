import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import and_, or_
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.claim_summary import ClaimSummary
from app.models.receipt import Receipt
from app.models.relief_limit import ReliefLimit

WARNING_THRESHOLD = Decimal("0.80")


def _category_status(*, claimed: Decimal, limit_amount: Decimal) -> str:
    if limit_amount <= 0:
        return "ok"
    if claimed >= limit_amount:
        return "full"
    if claimed >= limit_amount * WARNING_THRESHOLD:
        return "warning"
    return "ok"


class ClaimSummaryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _context_filters(
        *,
        context_type: str,
        org_id: uuid.UUID | None,
    ):
        filters = [ClaimSummary.context_type == context_type]
        if context_type == "corporate":
            filters.append(ClaimSummary.org_id == org_id)
        else:
            filters.append(ClaimSummary.org_id.is_(None))
        return filters

    @staticmethod
    def _receipt_context_filters(
        *,
        context_type: str,
        org_id: uuid.UUID | None,
    ):
        if context_type == "corporate":
            return [Receipt.org_id == org_id]
        return [Receipt.org_id.is_(None)]

    async def get(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        context_type: str = "individual",
        org_id: uuid.UUID | None = None,
    ) -> ClaimSummary | None:
        result = await self._db.execute(
            select(ClaimSummary).where(
                ClaimSummary.user_id == user_id,
                ClaimSummary.tax_year == tax_year,
                ClaimSummary.category == category,
                *self._context_filters(context_type=context_type, org_id=org_id),
            ),
        )
        return result.scalar_one_or_none()

    async def get_approved_total(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        context_type: str = "individual",
        org_id: uuid.UUID | None = None,
    ) -> Decimal:
        summary = await self.get(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
            context_type=context_type,
            org_id=org_id,
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
        context_type: str,
        org_id: uuid.UUID | None = None,
    ) -> ClaimSummary:
        summary = await self.get(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
            context_type=context_type,
            org_id=org_id,
        )

        if summary is None:
            now = datetime.now(UTC)
            summary = ClaimSummary(
                id=uuid.uuid4(),
                user_id=user_id,
                context_type=context_type,
                org_id=org_id,
                tax_year=tax_year,
                category=category,
                total_claimed=max(Decimal("0"), amount_delta),
                receipt_count=max(0, count_delta),
                last_updated=now,
            )
            self._db.sync_session.add(summary)
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
        context_type: str = "individual",
        org_id: uuid.UUID | None = None,
    ) -> Decimal:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.category == category,
            Receipt.deleted_at.is_(None),
            Receipt.status.in_(("pending", "flagged")),
            *self._receipt_context_filters(context_type=context_type, org_id=org_id),
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
        context_type: str = "individual",
        org_id: uuid.UUID | None = None,
    ) -> list[ClaimSummary]:
        result = await self._db.execute(
            select(ClaimSummary)
            .where(
                ClaimSummary.user_id == user_id,
                ClaimSummary.tax_year == tax_year,
                *self._context_filters(context_type=context_type, org_id=org_id),
            )
            .order_by(ClaimSummary.category),
        )
        return list(result.scalars().all())

    async def sync_summary(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        category: str,
        amount_delta: Decimal,
        count_delta: int,
        context_type: str,
        org_id: uuid.UUID | None = None,
    ) -> ClaimSummary:
        now = datetime.now(UTC)
        bind = self._db.get_bind()
        dialect = bind.dialect.name if bind is not None else "postgresql"

        if dialect == "postgresql":
            stmt = (
                pg_insert(ClaimSummary)
                .values(
                    user_id=user_id,
                    context_type=context_type,
                    org_id=org_id,
                    tax_year=tax_year,
                    category=category,
                    total_claimed=max(Decimal("0"), amount_delta),
                    receipt_count=max(0, count_delta),
                    last_updated=now,
                )
                .on_conflict_do_update(
                    index_elements=[
                        "user_id",
                        "tax_year",
                        "category",
                        "context_type",
                        "org_id",
                    ],
                    set_={
                        "total_claimed": ClaimSummary.total_claimed + amount_delta,
                        "receipt_count": ClaimSummary.receipt_count + count_delta,
                        "last_updated": now,
                    },
                )
                .returning(ClaimSummary)
            )
            result = await self._db.execute(stmt)
            return result.scalar_one()

        return await self.adjust(
            user_id=user_id,
            tax_year=tax_year,
            category=category,
            amount_delta=amount_delta,
            count_delta=count_delta,
            context_type=context_type,
            org_id=org_id,
        )

    async def get_summary(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        context_type: str,
        org_id: uuid.UUID | None = None,
    ) -> list[dict]:
        limits_result = await self._db.execute(
            select(ReliefLimit)
            .where(ReliefLimit.is_active.is_(True))
            .order_by(ReliefLimit.sort_order, ReliefLimit.category),
        )
        active_limits = list(limits_result.scalars().all())
        summaries = await self.list_for_user(
            user_id=user_id,
            tax_year=tax_year,
            context_type=context_type,
            org_id=org_id,
        )
        summary_by_category = {item.category: item for item in summaries}

        rows: list[dict] = []
        for limit in active_limits:
            summary = summary_by_category.get(limit.category)
            total_claimed = summary.total_claimed if summary else Decimal("0")
            receipt_count = summary.receipt_count if summary else 0
            limit_amount = Decimal(str(limit.limit_amount))
            remaining = max(Decimal("0"), limit_amount - total_claimed)
            percentage = float(
                (total_claimed / limit_amount * 100).quantize(Decimal("0.1"))
                if limit_amount > 0
                else 0.0,
            )
            rows.append(
                {
                    "category": limit.category,
                    "be_seksyen": limit.be_seksyen,
                    "limit_amount": limit_amount,
                    "total_claimed": total_claimed,
                    "remaining": remaining,
                    "percentage": percentage,
                    "receipt_count": receipt_count,
                    "status": _category_status(
                        claimed=total_claimed,
                        limit_amount=limit_amount,
                    ),
                },
            )
        return rows
