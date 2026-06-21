import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import decrypt_secret, encrypt_secret, mask_secret
from app.core.exceptions import AppError
from app.core.secret_keys import ALLOWED_SECRET_KEYS
from app.repositories.system_setting import SystemSettingRepository
from app.schemas.config_secrets import SecretSettingMaskedRead
from app.core.openrouter_key import validate_openrouter_key_format
from app.services.audit import AuditService


class SecretSettingsService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._settings = SystemSettingRepository(db)

    async def list_masked(self) -> list[SecretSettingMaskedRead]:
        stored = {item.key: item for item in await self._settings.list_all()}
        results: list[SecretSettingMaskedRead] = []

        for key in sorted(ALLOWED_SECRET_KEYS):
            item = stored.get(key)
            if item is None:
                results.append(
                    SecretSettingMaskedRead(
                        key=key,
                        masked_value=None,
                        is_configured=False,
                        updated_at=None,
                    ),
                )
                continue

            raw = decrypt_secret(item.encrypted_value)
            results.append(
                SecretSettingMaskedRead(
                    key=key,
                    masked_value=mask_secret(raw),
                    is_configured=True,
                    updated_at=item.updated_at,
                ),
            )

        return results

    async def get_secret(self, key: str) -> str | None:
        self._validate_key(key)
        item = await self._settings.get_by_key(key)
        if item is None:
            return None
        return decrypt_secret(item.encrypted_value)

    async def set_secret(
        self,
        key: str,
        raw_value: str,
        *,
        updated_by: uuid.UUID,
    ) -> SecretSettingMaskedRead:
        self._validate_key(key)
        cleaned = raw_value.strip()
        if key == "openrouter_api_key":
            valid, message = validate_openrouter_key_format(cleaned)
            if not valid:
                raise AppError(
                    message=message,
                    code="VALIDATION_ERROR",
                    status_code=422,
                )

        encrypted = encrypt_secret(cleaned)
        item = await self._settings.upsert(
            key=key,
            encrypted_value=encrypted,
            updated_by=updated_by,
        )
        await self._db.flush()

        await AuditService(self._db).log(
            action="secret.updated",
            user_id=updated_by,
            resource="secret",
            metadata={"key": key},
        )

        return SecretSettingMaskedRead(
            key=item.key,
            masked_value=mask_secret(cleaned),
            is_configured=True,
            updated_at=item.updated_at,
        )

    async def bulk_set_secrets(
        self,
        secrets: dict[str, str],
        *,
        updated_by: uuid.UUID,
    ) -> list[SecretSettingMaskedRead]:
        results: list[SecretSettingMaskedRead] = []
        for key, value in secrets.items():
            result = await self.set_secret(key, value, updated_by=updated_by)
            results.append(result)
        return results

    def _validate_key(self, key: str) -> None:
        if key not in ALLOWED_SECRET_KEYS:
            raise AppError(
                message=f"Kunci rahsia '{key}' tidak dibenarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )
