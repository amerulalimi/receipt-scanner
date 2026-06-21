from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class SpouseLink(Base, TimestampMixin):
    __tablename__ = "spouse_links"
    __table_args__ = (
        Index("idx_spouse_links_requester", "requester_id"),
        Index("idx_spouse_links_partner", "partner_id"),
        Index("idx_spouse_links_partner_email", "partner_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
    )
    partner_email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    requester = relationship("User", foreign_keys=[requester_id])
    partner = relationship("User", foreign_keys=[partner_id])

    def mark_responded(self, *, status: str, partner_id: uuid.UUID | None = None) -> None:
        self.status = status
        self.responded_at = datetime.now(UTC)
        if partner_id is not None:
            self.partner_id = partner_id
