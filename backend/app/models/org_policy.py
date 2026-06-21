from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.organisation import Organisation

DEFAULT_ALLOWED_CATEGORIES = [
    "perubatan",
    "gaya_hidup",
    "sukan",
    "pendidikan",
    "sspn",
    "ev_charging",
]


class OrgPolicy(Base):
    __tablename__ = "org_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    allowed_categories: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)),
        server_default=text(
            "ARRAY['perubatan', 'gaya_hidup', 'sukan', "
            "'pendidikan', 'sspn', 'ev_charging']::varchar(50)[]"
        ),
    )
    require_hr_approval: Mapped[bool] = mapped_column(Boolean, server_default="true")
    max_receipts_per_month: Mapped[int] = mapped_column(Integer, server_default="50")
    tax_year: Mapped[int] = mapped_column(SmallInteger, server_default="2025")
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    organisation: Mapped[Organisation] = relationship(back_populates="org_policy")
