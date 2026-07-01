import uuid
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt_line_item import ReceiptLineItem


class ReceiptLineItemRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_receipt(self, receipt_id: uuid.UUID) -> list[ReceiptLineItem]:
        result = await self._db.execute(
            select(ReceiptLineItem)
            .where(ReceiptLineItem.receipt_id == receipt_id)
            .order_by(ReceiptLineItem.sort_order, ReceiptLineItem.created_at),
        )
        return list(result.scalars().all())

    async def delete_for_receipt(self, receipt_id: uuid.UUID) -> None:
        await self._db.execute(
            delete(ReceiptLineItem).where(ReceiptLineItem.receipt_id == receipt_id),
        )

    async def create_many(
        self,
        receipt_id: uuid.UUID,
        items: list[dict],
    ) -> list[ReceiptLineItem]:
        created: list[ReceiptLineItem] = []
        for index, item in enumerate(items):
            line_item = ReceiptLineItem(
                id=uuid.uuid4(),
                receipt_id=receipt_id,
                sort_order=index,
                description=item["description"],
                amount=Decimal(str(item["amount"])),
                category=item["category"],
                ai_claimable=item["ai_claimable"],
                included_in_claim=item["included_in_claim"],
            )
            self._db.add(line_item)
            created.append(line_item)
        await self._db.flush()
        return created

    async def get_by_ids_for_receipt(
        self,
        receipt_id: uuid.UUID,
        item_ids: list[uuid.UUID],
    ) -> list[ReceiptLineItem]:
        if not item_ids:
            return []
        result = await self._db.execute(
            select(ReceiptLineItem).where(
                ReceiptLineItem.receipt_id == receipt_id,
                ReceiptLineItem.id.in_(item_ids),
            ),
        )
        return list(result.scalars().all())
