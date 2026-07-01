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
        org_id: uuid.UUID | None,
        *,
        include_flags: bool = False,
        include_line_items: bool = False,
    ) -> Receipt | None:
        conditions = [
            Receipt.id == receipt_id,
            Receipt.user_id == user_id,
            Receipt.deleted_at.is_(None),
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        stmt = select(Receipt).where(*conditions)
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

    async def get_by_content_hash_for_user(
        self,
        content_hash: str,
        user_id: uuid.UUID,
    ) -> Receipt | None:
        """Find original (non-duplicate) receipt by raw content SHA-256 for a user."""
        result = await self._db.execute(
            select(Receipt).where(
                Receipt.user_id == user_id,
                Receipt.image_hash == content_hash,
                Receipt.deleted_at.is_(None),
                Receipt.status != "duplicate",
            ),
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
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
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
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
            .options(selectinload(Receipt.flags))
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
            .options(selectinload(Receipt.flags))
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
        org_id: uuid.UUID | None,
        tax_year: int,
    ) -> dict[str, int]:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.tax_year == tax_year,
            Receipt.deleted_at.is_(None),
            Receipt.category.is_not(None),
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        result = await self._db.execute(
            select(Receipt.category, func.count()).where(*conditions).group_by(Receipt.category),
        )
        return {category: int(count) for category, count in result.all() if category}

    async def sum_claimed_this_month(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
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
        if org_id is None:
            month_conditions.append(Receipt.org_id.is_(None))
        else:
            month_conditions.append(Receipt.org_id == org_id)

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

    async def count_uploads_this_month(
        self,
        *,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
        month_start: date,
        month_end: date,
    ) -> int:
        conditions = [
            Receipt.user_id == user_id,
            Receipt.deleted_at.is_(None),
            Receipt.status != "duplicate",
            func.coalesce(
                Receipt.receipt_date,
                func.cast(Receipt.created_at, sa.Date),
            )
            >= month_start,
            func.coalesce(
                Receipt.receipt_date,
                func.cast(Receipt.created_at, sa.Date),
            )
            <= month_end,
        ]
        if org_id is None:
            conditions.append(Receipt.org_id.is_(None))
        else:
            conditions.append(Receipt.org_id == org_id)
        result = await self._db.execute(
            select(func.count()).select_from(Receipt).where(*conditions),
        )
        return int(result.scalar_one())

    async def create(self, receipt: Receipt) -> Receipt:
        if receipt.id is None:
            receipt.id = uuid.uuid4()
        self._db.sync_session.add(receipt)
        await self._db.flush()
        await self._db.refresh(receipt)
        return receipt

    async def create_receipt(self, receipt: Receipt) -> Receipt:
        return await self.create(receipt)

    async def get_receipt(
        self,
        receipt_id: uuid.UUID,
        user_id: uuid.UUID,
        *,
        include_flags: bool = False,
        include_line_items: bool = False,
    ) -> Receipt | None:
        return await self.get_by_id_for_user(
            receipt_id,
            user_id,
            org_id=None,
            include_flags=include_flags,
            include_line_items=include_line_items,
        )

    async def get_receipts(
        self,
        user_id: uuid.UUID,
        *,
        tax_year: int | None = None,
        category: str | None = None,
        status: str | None = None,
        page: int = 1,
        limit: int = 20,
        sort: str = "created_at:desc",
    ) -> tuple[list[Receipt], int]:
        sort_field, _, sort_order = sort.partition(":")
        sort_field = sort_field or "created_at"
        sort_order = sort_order or "desc"
        return await self.list_for_user(
            user_id=user_id,
            org_id=None,
            tax_year=tax_year,
            category=category,
            status=status,
            page=page,
            limit=limit,
            sort_field=sort_field,
            sort_order=sort_order,
        )

    async def update_receipt(self, receipt: Receipt) -> Receipt:
        await self._db.flush()
        await self._db.refresh(receipt)
        return receipt

    async def soft_delete_receipt(
        self,
        receipt_id: uuid.UUID,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
    ) -> bool:
        receipt = await self.get_by_id_for_user(receipt_id, user_id, org_id)
        if receipt is None:
            return False
        await self.soft_delete(receipt)
        return True

    async def create_flag(
        self,
        receipt_id: uuid.UUID,
        flag_type: str,
        message: str | None,
    ) -> None:
        from datetime import UTC, datetime

        from app.models.receipt_flag import ReceiptFlag

        flag = ReceiptFlag(
            id=uuid.uuid4(),
            receipt_id=receipt_id,
            flag_type=flag_type,
            message=message,
            created_at=datetime.now(UTC),
        )
        self._db.sync_session.add(flag)
        await self._db.flush()

    async def get_receipt_with_details(
        self,
        receipt_id: uuid.UUID,
        user_id: uuid.UUID,
        org_id: uuid.UUID | None,
    ) -> Receipt | None:
        return await self.get_by_id_for_user(
            receipt_id,
            user_id,
            org_id,
            include_flags=True,
            include_line_items=True,
        )

    async def soft_delete(self, receipt: Receipt) -> Receipt:
        receipt.deleted_at = datetime.now(UTC)
        await self._db.flush()
        await self._db.refresh(receipt)
        return receipt
