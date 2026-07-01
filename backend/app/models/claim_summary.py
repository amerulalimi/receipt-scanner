from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class ClaimSummary(Base):
    __tablename__ = "claim_summaries"
    __table_args__ = (
        CheckConstraint(
            "context_type IN ('individual', 'corporate')",
            name="ck_claim_summaries_context_type",
        ),
        UniqueConstraint(
            "user_id",
            "tax_year",
            "category",
            "context_type",
            "org_id",
            name="uq_claim_summaries_user_year_category_context",
        ),
        Index("idx_summary_user_year", "user_id", "tax_year"),
        Index("idx_summary_context", "user_id", "context_type", "org_id", "tax_year"),
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
    context_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default="individual")
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
    )
    tax_year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    total_claimed: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        server_default="0",
    )
    receipt_count: Mapped[int] = mapped_column(Integer, server_default="0")
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="claim_summaries")
