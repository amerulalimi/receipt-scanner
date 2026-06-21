import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: uuid.UUID | None,
        org_id: uuid.UUID | None,
        action: str,
        resource: str | None,
        resource_id: uuid.UUID | None,
        metadata: dict | None,
        ip_address: str | None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            org_id=org_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            metadata_=metadata,
            ip_address=ip_address,
        )
        self._db.add(entry)
        await self._db.flush()
        await self._db.refresh(entry)
        return entry

    async def list_recent(
        self,
        *,
        action: str | None,
        page: int,
        limit: int,
    ) -> tuple[list[AuditLog], int]:
        conditions = []
        if action:
            conditions.append(AuditLog.action == action)

        count_result = await self._db.execute(
            select(func.count()).select_from(AuditLog).where(*conditions),
        )
        total = int(count_result.scalar_one())

        offset = (page - 1) * limit
        result = await self._db.execute(
            select(AuditLog)
            .where(*conditions)
            .order_by(AuditLog.created_at.desc())
            .offset(offset)
            .limit(limit),
        )
        return list(result.scalars().all()), total

    async def delete_older_than(self, cutoff: datetime) -> int:
        result = await self._db.execute(
            select(AuditLog).where(AuditLog.created_at < cutoff),
        )
        entries = list(result.scalars().all())
        for entry in entries:
            await self._db.delete(entry)
        await self._db.flush()
        return len(entries)
