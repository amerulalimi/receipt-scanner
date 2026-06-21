from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.invite_token import InviteToken
    from app.models.org_policy import OrgPolicy
    from app.models.receipt import Receipt
    from app.models.user import User


class Organisation(Base, TimestampMixin):
    __tablename__ = "organisations"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended')",
            name="ck_organisations_status",
        ),
        Index("idx_org_domain", "email_domain"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ssm_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    email_domain: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    domain_verified: Mapped[bool] = mapped_column(Boolean, server_default="false")
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="active",
        nullable=False,
    )

    users: Mapped[list[User]] = relationship(back_populates="organisation")
    invite_tokens: Mapped[list[InviteToken]] = relationship(back_populates="organisation")
    receipts: Mapped[list[Receipt]] = relationship(back_populates="organisation")
    org_policy: Mapped[OrgPolicy | None] = relationship(
        back_populates="organisation",
        uselist=False,
    )
