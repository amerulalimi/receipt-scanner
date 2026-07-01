import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.platform_admin import PlatformAdmin


class PlatformAdminRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_email(self, email: str) -> PlatformAdmin | None:
        result = await self._db.execute(
            select(PlatformAdmin).where(PlatformAdmin.email == email),
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, admin_id: uuid.UUID) -> PlatformAdmin | None:
        result = await self._db.execute(
            select(PlatformAdmin).where(PlatformAdmin.id == admin_id),
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        full_name: str | None = None,
    ) -> PlatformAdmin:
        admin = PlatformAdmin(
            id=uuid.uuid4(),
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_active=True,
        )
        self._db.add(admin)
        await self._db.flush()
        await self._db.refresh(admin)
        return admin

    async def update_last_login(self, admin_id: uuid.UUID, *, at: datetime) -> None:
        admin = await self.get_by_id(admin_id)
        if admin is None:
            return
        admin.last_login_at = at
        await self._db.flush()
