import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_preference import NotificationPreference


class NotificationPreferenceRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, user_id: uuid.UUID) -> NotificationPreference | None:
        result = await self._db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_or_create(self, user_id: uuid.UUID) -> NotificationPreference:
        preference = await self.get(user_id)
        if preference is not None:
            return preference

        preference = NotificationPreference(user_id=user_id)
        self._db.add(preference)
        await self._db.flush()
        await self._db.refresh(preference)
        return preference

    async def update(
        self,
        preference: NotificationPreference,
        *,
        email_enabled: bool | None = None,
        in_app_enabled: bool | None = None,
        digest_frequency: str | None = None,
        last_monthly_digest_at: datetime | None = None,
    ) -> NotificationPreference:
        if email_enabled is not None:
            preference.email_enabled = email_enabled
        if in_app_enabled is not None:
            preference.in_app_enabled = in_app_enabled
        if digest_frequency is not None:
            preference.digest_frequency = digest_frequency
        if last_monthly_digest_at is not None:
            preference.last_monthly_digest_at = last_monthly_digest_at

        preference.updated_at = datetime.now(UTC)
        await self._db.flush()
        await self._db.refresh(preference)
        return preference

    async def list_users_due_for_digest(
        self,
        *,
        month_start: datetime,
    ) -> list[uuid.UUID]:
        result = await self._db.execute(
            select(NotificationPreference.user_id).where(
                NotificationPreference.email_enabled.is_(True),
                NotificationPreference.digest_frequency == "monthly",
                (
                    NotificationPreference.last_monthly_digest_at.is_(None)
                    | (NotificationPreference.last_monthly_digest_at < month_start)
                ),
            ),
        )
        return list(result.scalars().all())
