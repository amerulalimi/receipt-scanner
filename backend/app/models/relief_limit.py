from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReliefLimit(Base):
    __tablename__ = "relief_limits"
    __table_args__ = (
        UniqueConstraint("category", name="uq_relief_limits_category"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    be_seksyen: Mapped[str | None] = mapped_column(String(20))
    limit_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description_en: Mapped[str | None] = mapped_column(Text)
    description_my: Mapped[str | None] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(SmallInteger, server_default="0", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
