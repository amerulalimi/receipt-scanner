from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.organisation import Organisation
    from app.models.receipt_flag import ReceiptFlag
    from app.models.receipt_line_item import ReceiptLineItem
    from app.models.user import User


class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'flagged', 'duplicate')",
            name="ck_receipts_status",
        ),
        CheckConstraint(
            "scan_status IN ('waiting', 'processing', 'success', 'failed')",
            name="ck_receipts_scan_status",
        ),
        Index("idx_receipt_user", "user_id"),
        Index("idx_receipt_org", "org_id"),
        Index("idx_receipt_category", "category"),
        Index("idx_receipt_status", "status"),
        Index("idx_receipt_year", "tax_year"),
        Index("idx_receipt_hash", "image_hash"),
        Index(
            "idx_receipt_deleted",
            "deleted_at",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="SET NULL"),
    )
    tax_year: Mapped[int] = mapped_column(SmallInteger, server_default="2025", nullable=False)

    image_key: Mapped[str] = mapped_column(String(512), nullable=False)
    image_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_type: Mapped[str | None] = mapped_column(String(10))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)

    merchant_name: Mapped[str | None] = mapped_column(String(255))
    receipt_date: Mapped[date | None] = mapped_column(Date)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    ocr_raw: Mapped[dict | None] = mapped_column(JSONB)
    ocr_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))

    category: Mapped[str | None] = mapped_column(String(50))
    be_seksyen: Mapped[str | None] = mapped_column(String(20))
    claimed_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    excluded_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        server_default="0",
    )
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    ai_nota: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(
        String(20),
        server_default="pending",
        nullable=False,
    )
    scan_status: Mapped[str] = mapped_column(
        String(20),
        server_default="waiting",
        nullable=False,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_comment: Mapped[str | None] = mapped_column(Text)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(
        back_populates="receipts",
        foreign_keys=[user_id],
    )
    organisation: Mapped[Organisation | None] = relationship(back_populates="receipts")
    flags: Mapped[list[ReceiptFlag]] = relationship(back_populates="receipt")
    line_items: Mapped[list[ReceiptLineItem]] = relationship(
        back_populates="receipt",
        order_by="ReceiptLineItem.sort_order",
        cascade="all, delete-orphan",
    )
