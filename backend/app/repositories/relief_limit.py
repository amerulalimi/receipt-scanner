import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import Receipt
from app.models.relief_limit import ReliefLimit


class ReliefLimitRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_active(self, *, category: str) -> ReliefLimit | None:
        result = await self._db.execute(
            select(ReliefLimit).where(
                ReliefLimit.category == category,
                ReliefLimit.is_active.is_(True),
            ),
        )
        return result.scalar_one_or_none()

    async def list_active(self) -> list[ReliefLimit]:
        result = await self._db.execute(
            select(ReliefLimit)
            .where(ReliefLimit.is_active.is_(True))
            .order_by(ReliefLimit.sort_order, ReliefLimit.category),
        )
        return list(result.scalars().all())

    async def list_all(self) -> list[ReliefLimit]:
        result = await self._db.execute(
            select(ReliefLimit).order_by(ReliefLimit.sort_order, ReliefLimit.category),
        )
        return list(result.scalars().all())

    async def get_by_category(self, category: str) -> ReliefLimit | None:
        result = await self._db.execute(
            select(ReliefLimit).where(ReliefLimit.category == category),
        )
        return result.scalar_one_or_none()

    async def category_exists(self, category: str) -> bool:
        result = await self._db.execute(
            select(func.count())
            .select_from(ReliefLimit)
            .where(ReliefLimit.category == category),
        )
        return int(result.scalar_one()) > 0

    async def count_receipts_for_category(self, category: str) -> int:
        result = await self._db.execute(
            select(func.count())
            .select_from(Receipt)
            .where(
                Receipt.category == category,
                Receipt.deleted_at.is_(None),
            ),
        )
        return int(result.scalar_one())

    async def create(
        self,
        *,
        category: str,
        limit_amount: Decimal,
        be_seksyen: str | None,
        description_my: str | None,
        sort_order: int,
        updated_by: uuid.UUID,
    ) -> ReliefLimit:
        item = ReliefLimit(
            category=category,
            limit_amount=limit_amount,
            be_seksyen=be_seksyen,
            description_my=description_my,
            sort_order=sort_order,
            updated_by=updated_by,
        )
        self._db.add(item)
        await self._db.flush()
        await self._db.refresh(item)
        return item

    async def update(
        self,
        item: ReliefLimit,
        *,
        limit_amount: Decimal | None = None,
        be_seksyen: str | None = None,
        description_my: str | None = None,
        is_active: bool | None = None,
        sort_order: int | None = None,
        updated_by: uuid.UUID,
    ) -> ReliefLimit:
        if limit_amount is not None:
            item.limit_amount = limit_amount
        if be_seksyen is not None:
            item.be_seksyen = be_seksyen
        if description_my is not None:
            item.description_my = description_my
        if is_active is not None:
            item.is_active = is_active
        if sort_order is not None:
            item.sort_order = sort_order
        item.updated_by = updated_by
        await self._db.flush()
        await self._db.refresh(item)
        return item
