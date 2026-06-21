from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import Receipt
from app.models.user import User
from app.repositories.relief_limit import ReliefLimitRepository
from app.schemas.org_analytics import (
    OrgAnalyticsCategoryTrend,
    OrgAnalyticsData,
    OrgAnalyticsEmployeeRank,
    OrgAnalyticsForecast,
    OrgAnalyticsRejectionReason,
    OrgAnalyticsTurnaround,
)


class OrgAnalyticsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._limits = ReliefLimitRepository(db)

    async def get_analytics(
        self,
        org_id: uuid.UUID,
        *,
        tax_year: int,
    ) -> OrgAnalyticsData:
        category_trend = await self._category_trend(org_id, tax_year)
        top_employees = await self._top_employees(org_id, tax_year)
        turnaround = await self._approval_turnaround(org_id, tax_year)
        rejections = await self._rejection_breakdown(org_id, tax_year)
        forecast = await self._forecast(org_id, tax_year)
        return OrgAnalyticsData(
            tax_year=tax_year,
            category_trend=category_trend,
            top_employees=top_employees,
            turnaround=turnaround,
            rejections=rejections,
            forecast=forecast,
        )

    async def _category_trend(
        self,
        org_id: uuid.UUID,
        tax_year: int,
    ) -> list[OrgAnalyticsCategoryTrend]:
        result = await self._db.execute(
            select(
                Receipt.category,
                func.date_trunc("month", Receipt.reviewed_at).label("month"),
                func.coalesce(func.sum(Receipt.claimed_amount), 0),
            )
            .where(
                Receipt.org_id == org_id,
                Receipt.tax_year == tax_year,
                Receipt.status == "approved",
                Receipt.deleted_at.is_(None),
                Receipt.reviewed_at.is_not(None),
            )
            .group_by(Receipt.category, "month")
            .order_by("month"),
        )
        return [
            OrgAnalyticsCategoryTrend(
                category=category or "unknown",
                month=month.date() if month else None,
                total_claimed=Decimal(str(total)),
            )
            for category, month, total in result.all()
        ]

    async def _top_employees(
        self,
        org_id: uuid.UUID,
        tax_year: int,
    ) -> list[OrgAnalyticsEmployeeRank]:
        result = await self._db.execute(
            select(
                User.id,
                User.full_name,
                User.email,
                func.coalesce(func.sum(Receipt.claimed_amount), 0),
                func.count(Receipt.id),
            )
            .join(Receipt, Receipt.user_id == User.id)
            .where(
                User.org_id == org_id,
                Receipt.tax_year == tax_year,
                Receipt.status == "approved",
                Receipt.deleted_at.is_(None),
            )
            .group_by(User.id, User.full_name, User.email)
            .order_by(desc(func.coalesce(func.sum(Receipt.claimed_amount), 0)))
            .limit(10),
        )
        return [
            OrgAnalyticsEmployeeRank(
                user_id=user_id,
                full_name=full_name,
                email=email,
                total_claimed=Decimal(str(total)),
                receipt_count=int(count),
            )
            for user_id, full_name, email, total, count in result.all()
        ]

    async def _approval_turnaround(
        self,
        org_id: uuid.UUID,
        tax_year: int,
    ) -> OrgAnalyticsTurnaround:
        result = await self._db.execute(
            select(
                func.avg(
                    func.extract(
                        "epoch",
                        Receipt.reviewed_at - Receipt.created_at,
                    ),
                ),
                func.count(Receipt.id),
            )
            .where(
                Receipt.org_id == org_id,
                Receipt.tax_year == tax_year,
                Receipt.status.in_(("approved", "rejected")),
                Receipt.reviewed_at.is_not(None),
                Receipt.deleted_at.is_(None),
            ),
        )
        avg_seconds, count = result.one()
        hours = float(avg_seconds or 0) / 3600 if avg_seconds else 0.0
        return OrgAnalyticsTurnaround(
            average_hours=round(hours, 1),
            reviewed_count=int(count or 0),
        )

    async def _rejection_breakdown(
        self,
        org_id: uuid.UUID,
        tax_year: int,
    ) -> list[OrgAnalyticsRejectionReason]:
        result = await self._db.execute(
            select(Receipt.review_comment, func.count(Receipt.id))
            .where(
                Receipt.org_id == org_id,
                Receipt.tax_year == tax_year,
                Receipt.status == "rejected",
                Receipt.deleted_at.is_(None),
            )
            .group_by(Receipt.review_comment)
            .order_by(desc(func.count(Receipt.id))),
        )
        return [
            OrgAnalyticsRejectionReason(
                reason=reason or "No comment",
                count=int(count),
            )
            for reason, count in result.all()
        ]

    async def _forecast(
        self,
        org_id: uuid.UUID,
        tax_year: int,
    ) -> list[OrgAnalyticsForecast]:
        now = datetime.now(UTC)
        month = now.month
        if month <= 0:
            month = 1

        result = await self._db.execute(
            select(
                Receipt.category,
                func.coalesce(func.sum(Receipt.claimed_amount), 0),
            )
            .where(
                Receipt.org_id == org_id,
                Receipt.tax_year == tax_year,
                Receipt.status == "approved",
                Receipt.deleted_at.is_(None),
            )
            .group_by(Receipt.category),
        )
        approved_by_category = {
            category or "unknown": Decimal(str(total))
            for category, total in result.all()
        }

        limits = await self._limits.list_active()
        forecasts: list[OrgAnalyticsForecast] = []
        for limit in limits:
            claimed = approved_by_category.get(limit.category, Decimal("0"))
            projected = (claimed / Decimal(str(month))) * Decimal("12")
            limit_amount = Decimal(str(limit.limit_amount))
            forecasts.append(
                OrgAnalyticsForecast(
                    category=limit.category,
                    approved_to_date=claimed,
                    projected_year_end=projected.quantize(Decimal("0.01")),
                    org_limit=limit_amount,
                    utilization_pct=float(
                        (projected / limit_amount * 100).quantize(Decimal("0.1"))
                        if limit_amount > 0
                        else Decimal("0"),
                    ),
                ),
            )
        return forecasts
