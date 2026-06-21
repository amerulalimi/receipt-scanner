from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UploadSession(Base):
    __tablename__ = "upload_sessions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'warned', 'expired', 'closed')",
            name="ck_upload_sessions_status",
        ),
        Index("idx_upload_session_token", "token"),
        Index("idx_upload_session_user", "user_id"),
        Index("idx_upload_session_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    token: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    desktop_session: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="active",
        nullable=False,
    )
    tax_year: Mapped[int] = mapped_column(Integer, server_default="2025", nullable=False)
    inactivity_secs: Mapped[int] = mapped_column(Integer, server_default="600")
    last_upload_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    uploads_count: Mapped[int] = mapped_column(Integer, server_default="0")
    mobile_ua: Mapped[str | None] = mapped_column(String(500))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="upload_sessions")
