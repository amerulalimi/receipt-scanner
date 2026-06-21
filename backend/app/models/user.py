from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.claim_summary import ClaimSummary
    from app.models.invite_token import InviteToken
    from app.models.notification_preference import NotificationPreference
    from app.models.organisation import Organisation
    from app.models.receipt import Receipt
    from app.models.upload_session import UploadSession
    from app.models.user_notification import UserNotification


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('individual', 'employee', 'hr_admin', 'superadmin')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "account_type IN ('individual', 'corporate')",
            name="ck_users_account_type",
        ),
        Index("idx_user_email", "email"),
        Index("idx_user_org", "org_id"),
        Index("idx_user_role", "role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    account_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="individual",
    )
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organisations.id", ondelete="SET NULL"),
    )
    tax_year: Mapped[int] = mapped_column(SmallInteger, server_default="2025")
    tax_bracket: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    email_verified: Mapped[bool] = mapped_column(Boolean, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    org_employee_code: Mapped[str | None] = mapped_column(String(50))
    forwarding_token: Mapped[str | None] = mapped_column(String(32))

    organisation: Mapped[Organisation | None] = relationship(back_populates="users")
    receipts: Mapped[list[Receipt]] = relationship(
        back_populates="user",
        foreign_keys="Receipt.user_id",
    )
    upload_sessions: Mapped[list[UploadSession]] = relationship(back_populates="user")
    claim_summaries: Mapped[list[ClaimSummary]] = relationship(back_populates="user")
    invites_created: Mapped[list[InviteToken]] = relationship(
        back_populates="invited_by_user",
        foreign_keys="InviteToken.invited_by",
    )
    notification_preference: Mapped[NotificationPreference | None] = relationship(
        back_populates="user",
        uselist=False,
    )
    notifications: Mapped[list[UserNotification]] = relationship(
        back_populates="user",
    )
