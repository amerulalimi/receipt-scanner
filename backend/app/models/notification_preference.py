from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class NotificationPreference(Base, TimestampMixin):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        CheckConstraint(
            "digest_frequency IN ('off', 'monthly')",
            name="ck_notification_preferences_digest_frequency",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    email_enabled: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    in_app_enabled: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    digest_frequency: Mapped[str] = mapped_column(
        String(20),
        server_default="monthly",
        nullable=False,
    )
    last_monthly_digest_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )

    user: Mapped[User] = relationship(back_populates="notification_preference")
