from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.secret_keys import CONFIG_DEFAULTS
from app.models.receipt import Receipt
from app.models.upload_session import UploadSession
from app.repositories.audit_log import AuditLogRepository
from app.services.system_config import SystemConfigService


class RetentionService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._config = SystemConfigService(db)
        self._audit_logs = AuditLogRepository(db)

    async def _get_retention_days(self, key: str) -> int:
        raw = await self._config.get(key)
        if not raw:
            raw = CONFIG_DEFAULTS.get(key, "90")
        try:
            days = int(raw)
        except ValueError as exc:
            raise AppError(
                message=f"Konfigurasi '{key}' tidak sah.",
                code="VALIDATION_ERROR",
                status_code=422,
            ) from exc
        if days < 1:
            raise AppError(
                message=f"Konfigurasi '{key}' mestilah sekurang-kurangnya 1 hari.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
        return days

    async def purge(self) -> dict[str, int]:
        audit_days = await self._get_retention_days("audit_retention_days")
        receipt_days = await self._get_retention_days("receipt_retention_days")

        audit_cutoff = datetime.now(UTC) - timedelta(days=audit_days)
        receipt_cutoff = datetime.now(UTC) - timedelta(days=receipt_days)

        audit_deleted = await self._audit_logs.delete_older_than(audit_cutoff)

        result = await self._db.execute(
            select(Receipt).where(
                Receipt.deleted_at.is_not(None),
                Receipt.deleted_at < receipt_cutoff,
            ),
        )
        stale_receipts = list(result.scalars().all())
        receipt_deleted = len(stale_receipts)
        if stale_receipts:
            await self._db.execute(
                delete(Receipt).where(
                    Receipt.id.in_([item.id for item in stale_receipts]),
                ),
            )
            await self._db.flush()

        session_cutoff = datetime.now(UTC) - timedelta(days=7)
        session_result = await self._db.execute(
            select(UploadSession).where(
                UploadSession.status.in_(("expired", "closed")),
                UploadSession.created_at < session_cutoff,
            ),
        )
        stale_sessions = list(session_result.scalars().all())
        sessions_deleted = len(stale_sessions)
        if stale_sessions:
            await self._db.execute(
                delete(UploadSession).where(
                    UploadSession.id.in_([item.id for item in stale_sessions]),
                ),
            )
            await self._db.flush()

        return {
            "audit_logs_deleted": audit_deleted,
            "receipts_deleted": receipt_deleted,
            "purged_receipts": receipt_deleted,
            "purged_sessions": sessions_deleted,
            "audit_retention_days": audit_days,
            "receipt_retention_days": receipt_days,
        }
