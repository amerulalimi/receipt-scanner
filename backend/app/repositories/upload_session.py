import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import Receipt
from app.models.upload_session import UploadSession


class UploadSessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_token(self, token: str) -> UploadSession | None:
        result = await self._db.execute(
            select(UploadSession).where(UploadSession.token == token),
        )
        return result.scalar_one_or_none()

    async def create(self, session: UploadSession) -> UploadSession:
        self._db.add(session)
        await self._db.flush()
        await self._db.refresh(session)
        return session

    async def update(self, session: UploadSession) -> UploadSession:
        await self._db.flush()
        await self._db.refresh(session)
        return session

    async def close_active_for_user(self, user_id: uuid.UUID) -> None:
        now = datetime.now(UTC)
        await self._db.execute(
            update(UploadSession)
            .where(
                UploadSession.user_id == user_id,
                UploadSession.status.in_(("active", "warned")),
            )
            .values(status="closed", closed_at=now),
        )

    async def sum_receipts_since(
        self,
        user_id: uuid.UUID,
        since: datetime,
    ) -> float:
        result = await self._db.execute(
            select(func.coalesce(func.sum(Receipt.total_amount), 0)).where(
                Receipt.user_id == user_id,
                Receipt.created_at >= since,
                Receipt.deleted_at.is_(None),
            ),
        )
        total = result.scalar_one()
        return float(total)
