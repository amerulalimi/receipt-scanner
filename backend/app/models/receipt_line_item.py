from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, Numeric, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.receipt import Receipt


class ReceiptLineItem(Base, TimestampMixin):
    __tablename__ = "receipt_line_items"
    __table_args__ = (Index("idx_receipt_line_items_receipt", "receipt_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="CASCADE"),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default="0", nullable=False)
    description: Mapped[str] = mapped_column(String(500), server_default="", nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    ai_claimable: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    included_in_claim: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        nullable=False,
    )

    receipt: Mapped[Receipt] = relationship(back_populates="line_items")
