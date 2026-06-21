import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_setting import SystemSetting


class SystemSettingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_key(self, key: str) -> SystemSetting | None:
        result = await self._db.execute(
            select(SystemSetting).where(SystemSetting.key == key),
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[SystemSetting]:
        result = await self._db.execute(
            select(SystemSetting).order_by(SystemSetting.key),
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        key: str,
        encrypted_value: str,
        updated_by: uuid.UUID,
    ) -> SystemSetting:
        existing = await self.get_by_key(key)
        if existing is None:
            setting = SystemSetting(
                key=key,
                encrypted_value=encrypted_value,
                updated_by=updated_by,
            )
            self._db.add(setting)
            await self._db.flush()
            await self._db.refresh(setting)
            return setting

        existing.encrypted_value = encrypted_value
        existing.updated_by = updated_by
        await self._db.flush()
        await self._db.refresh(existing)
        return existing
