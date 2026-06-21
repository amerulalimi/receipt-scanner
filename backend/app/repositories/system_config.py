import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.system_config import SystemConfig


class SystemConfigRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_key(self, key: str) -> SystemConfig | None:
        result = await self._db.execute(
            select(SystemConfig).where(SystemConfig.key == key),
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> list[SystemConfig]:
        result = await self._db.execute(
            select(SystemConfig).order_by(SystemConfig.key),
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        key: str,
        value: str,
        updated_by: uuid.UUID,
    ) -> SystemConfig:
        existing = await self.get_by_key(key)
        if existing is None:
            config = SystemConfig(
                key=key,
                value=value,
                updated_by=updated_by,
            )
            self._db.add(config)
            await self._db.flush()
            await self._db.refresh(config)
            return config

        existing.value = value
        existing.updated_by = updated_by
        await self._db.flush()
        await self._db.refresh(existing)
        return existing
