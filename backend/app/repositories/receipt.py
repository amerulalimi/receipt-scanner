import uuid
from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.receipt import Receipt
from app.models.user import User


class ReceiptRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(
        self,
        receipt_id: uuid.UUID,
        *,
        include_flags: bool = False,
        include_line_items: bool = False,
    ) -> Receipt | None:
        stmt = select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.deleted_at.is_(None),
        )
        if include_flags:
            stmt = stmt.options(selectinload(Receipt.flags))
        if include_line_items:
            stmt = stmt.options(selectinload(Receipt.line_items))

        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        receipt_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        include_flags: bool = False,
        include_line_items: bool = False,
    ) -> Receipt | None:
        stmt = select(Receipt).where(
            Receipt.id == receipt_id,
            Receipt.user_id == user_id,
            Receipt.deleted_at.is_(None),
        )
        if include_flags:
            stmt = stmt.options(selectinload(Receipt.flags))
        if include_line_items:
            stmt = stmt.options(selectinload(Receipt.line_items))

        result = await self._db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_image_hash(self, image_hash: str) -> Receipt | None:
        result = await self._db.execute(
            select(Receipt).where(
                Receipt.image_hash == image_hash,
                Receipt.deleted_at.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int | None,
        category: str | None,
        status: str | None,
        page: int,
        limit: int,
        sort_field: str,
        sort_order: str,
    ) -> tuple[list[Receipt], int]:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.deleted_at.is_(None),
        ]
        if tax_year is not None:
            conditions.append(Receipt.tax_year == tax_year)
        if category is not None:
            conditions.append(Receipt.category == category)
        if status is not None:
            conditions.append(Receipt.status == status)

        count_result = await self._db.execute(
            select(func.count()).select_from(Receipt).where(*conditions),
        )
        total = count_result.scalar_one()

        order_column = getattr(Receipt, sort_field, Receipt.created_at)
        ordering = desc(order_column) if sort_order == "desc" else asc(order_column)

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(Receipt)
            .where(*conditions)
            .order_by(ordering)
            .offset(offset)
            .limit(limit),
        )
        return list(result.scalars().all()), total

    async def list_pending_for_org(
        self,
        *,
        org_id: uuid.UUID,
        tax_year: int | None,
        page: int,
        limit: int,
    ) -> tuple[list[tuple[Receipt, User]], int]:
        conditions = [
            Receipt.org_id == org_id,
            Receipt.deleted_at.is_(None),
            Receipt.status.in_(("pending", "flagged")),
        ]
        if tax_year is not None:
            conditions.append(Receipt.tax_year == tax_year)

        count_result = await self._db.execute(
            select(func.count())
            .select_from(Receipt)
            .join(User, Receipt.user_id == User.id)
            .where(*conditions),
        )
        total = count_result.scalar_one()

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(Receipt, User)
            .join(User, Receipt.user_id == User.id)
            .where(*conditions)
            .order_by(desc(Receipt.created_at))
            .offset(offset)
            .limit(limit),
        )
        return list(result.all()), total

    async def list_all_pending_for_org(
        self,
        *,
        org_id: uuid.UUID,
        tax_year: int | None,
    ) -> list[Receipt]:
        conditions = [
            Receipt.org_id == org_id,
            Receipt.deleted_at.is_(None),
            Receipt.status.in_(("pending", "flagged")),
        ]
        if tax_year is not None:
            conditions.append(Receipt.tax_year == tax_year)

        result = await self._db.execute(
            select(Receipt).where(*conditions).order_by(desc(Receipt.created_at)),
        )
        return list(result.scalars().all())

    async def count_by_category_for_user_year(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
    ) -> dict[str, int]:
        result = await self._db.execute(
            select(Receipt.category, func.count())
            .where(
                Receipt.user_id == user_id,
                Receipt.tax_year == tax_year,
                Receipt.deleted_at.is_(None),
                Receipt.category.is_not(None),
            )
            .group_by(Receipt.category),
        )
        return {category: int(count) for category, count in result.all() if category}

    async def sum_claimed_this_month(
        self,
        *,
        user_id: uuid.UUID,
        tax_year: int,
        month_start: date,
        month_end: date,
    ) -> tuple[float, dict[str, float]]:
        effective_date = func.coalesce(
            Receipt.receipt_date,
            func.cast(Receipt.created_at, sa.Date),
        )
        month_conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.deleted_at.is_(None),
            Receipt.status == "approved",
            Receipt.claimed_amount.is_not(None),
            effective_date >= month_start,
            effective_date <= month_end,
        ]

        total_result = await self._db.execute(
            select(func.coalesce(func.sum(Receipt.claimed_amount), 0)).where(*month_conditions),
        )
        total = float(total_result.scalar_one())

        category_result = await self._db.execute(
            select(Receipt.category, func.coalesce(func.sum(Receipt.claimed_amount), 0))
            .where(*month_conditions)
            .group_by(Receipt.category),
        )
        by_category = {
            category: float(amount)
            for category, amount in category_result.all()
            if category
        }
        return total, by_category

    async def create(self, receipt: Receipt) -> Receipt:
        self._db.add(receipt)
        await self._db.flush()
        await self._db.refresh(receipt)
        return receipt

    async def soft_delete(self, receipt: Receipt) -> Receipt:
        receipt.deleted_at = datetime.now(UTC)
        await self._db.flush()
        await self._db.refresh(receipt)
        return receipt
