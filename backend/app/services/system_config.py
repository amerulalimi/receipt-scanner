import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.secret_keys import ALLOWED_CONFIG_KEYS, CONFIG_DEFAULTS
from app.repositories.system_config import SystemConfigRepository
from app.schemas.config_settings import SystemConfigRead


class SystemConfigService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._config = SystemConfigRepository(db)

    async def list_all(self) -> list[SystemConfigRead]:
        stored = {item.key: item for item in await self._config.list_all()}
        results: list[SystemConfigRead] = []

        for key in sorted(ALLOWED_CONFIG_KEYS):
            item = stored.get(key)
            if item is None:
                results.append(
                    SystemConfigRead(
                        key=key,
                        value=CONFIG_DEFAULTS.get(key, ""),
                        is_default=True,
                        updated_at=None,
                    ),
                )
                continue

            results.append(
                SystemConfigRead(
                    key=key,
                    value=item.value,
                    is_default=False,
                    updated_at=item.updated_at,
                ),
            )

        return results

    async def get(self, key: str) -> str:
        self._validate_key(key)
        item = await self._config.get_by_key(key)
        if item is None:
            return CONFIG_DEFAULTS.get(key, "")
        return item.value

    async def get_int(self, key: str, *, default: int) -> int:
        raw = await self.get(key)
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            return default

    async def set(
        self,
        key: str,
        value: str,
        *,
        updated_by: uuid.UUID,
    ) -> SystemConfigRead:
        self._validate_key(key)
        normalized = value.strip()
        if not normalized:
            raise AppError(
                message=f"Nilai untuk '{key}' tidak boleh kosong.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        item = await self._config.upsert(
            key=key,
            value=normalized,
            updated_by=updated_by,
        )
        await self._db.flush()

        return SystemConfigRead(
            key=item.key,
            value=item.value,
            is_default=False,
            updated_at=item.updated_at,
        )

    async def bulk_set(
        self,
        settings: dict[str, str],
        *,
        updated_by: uuid.UUID,
    ) -> list[SystemConfigRead]:
        results: list[SystemConfigRead] = []
        for key, value in settings.items():
            result = await self.set(key, value, updated_by=updated_by)
            results.append(result)
        return results

    def _validate_key(self, key: str) -> None:
        if key not in ALLOWED_CONFIG_KEYS:
            raise AppError(
                message=f"Kunci konfigurasi '{key}' tidak dibenarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
