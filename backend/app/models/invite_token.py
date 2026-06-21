from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.organisation import Organisation
    from app.models.user import User


class InviteToken(Base):
    __tablename__ = "invite_tokens"
    __table_args__ = (
        CheckConstraint(
            "role IN ('employee', 'hr_admin')",
            name="ck_invite_tokens_role",
        ),
        CheckConstraint(
            "invite_type IN ('email', 'link', 'csv')",
            name="ck_invite_tokens_invite_type",
        ),
        Index("idx_invite_token", "token"),
        Index("idx_invite_org", "org_id"),
        Index(
            "idx_invite_expiry",
            "expires_at",
            postgresql_where=text("used = FALSE"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    org_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="CASCADE"),
        nullable=False,
    )
    invited_email: Mapped[str | None] = mapped_column(String(255))
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        server_default="employee",
        nullable=False,
    )
    invite_type: Mapped[str] = mapped_column(String(20), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, server_default="false")
    used_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
    )
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    organisation: Mapped[Organisation] = relationship(back_populates="invite_tokens")
    invited_by_user: Mapped[User] = relationship(
        back_populates="invites_created",
        foreign_keys=[invited_by],
    )
