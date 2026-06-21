from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.audit_log import AuditLogRepository


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self._repo = AuditLogRepository(db)

    async def log(
        self,
        *,
        action: str,
        user_id: uuid.UUID | None = None,
        org_id: uuid.UUID | None = None,
        resource: str | None = None,
        resource_id: uuid.UUID | None = None,
        metadata: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        await self._repo.create(
            user_id=user_id,
            org_id=org_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            metadata=metadata,
            ip_address=ip_address,
        )
