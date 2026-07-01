import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_notification import UserNotification


class UserNotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id_for_user(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> UserNotification | None:
        result = await self._db.execute(
            select(UserNotification).where(
                UserNotification.id == notification_id,
                UserNotification.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def get_by_key(
        self,
        *,
        user_id: uuid.UUID,
        reminder_key: str,
    ) -> UserNotification | None:
        result = await self._db.execute(
            select(UserNotification).where(
                UserNotification.user_id == user_id,
                UserNotification.reminder_key == reminder_key,
            ),
        )
        return result.scalar_one_or_none()

    async def list_active_for_user(self, user_id: uuid.UUID) -> list[UserNotification]:
        now = datetime.now(UTC)
        result = await self._db.execute(
            select(UserNotification)
            .where(
                UserNotification.user_id == user_id,
                UserNotification.dismissed_at.is_(None),
                (UserNotification.expires_at.is_(None) | (UserNotification.expires_at > now)),
            )
            .order_by(UserNotification.created_at.desc()),
        )
        return list(result.scalars().all())

    async def upsert(
        self,
        *,
        user_id: uuid.UUID,
        reminder_key: str,
        type: str,
        severity: str,
        title_my: str,
        title_en: str,
        message_my: str,
        message_en: str,
        action_href: str | None,
        expires_at: datetime | None,
    ) -> UserNotification:
        existing = await self.get_by_key(user_id=user_id, reminder_key=reminder_key)
        if existing is not None:
            if existing.dismissed_at is not None:
                return existing

            existing.type = type
            existing.severity = severity
            existing.title_my = title_my
            existing.title_en = title_en
            existing.message_my = message_my
            existing.message_en = message_en
            existing.action_href = action_href
            existing.expires_at = expires_at
            await self._db.flush()
            await self._db.refresh(existing)
            return existing

        notification = UserNotification(
            id=uuid.uuid4(),
            user_id=user_id,
            reminder_key=reminder_key,
            type=type,
            severity=severity,
            title_my=title_my,
            title_en=title_en,
            message_my=message_my,
            message_en=message_en,
            action_href=action_href,
            expires_at=expires_at,
            created_at=datetime.now(UTC),
        )
        self._db.add(notification)
        await self._db.flush()
        await self._db.refresh(notification)
        return notification

    async def dismiss(self, notification: UserNotification) -> UserNotification:
        notification.dismissed_at = datetime.now(UTC)
        await self._db.flush()
        await self._db.refresh(notification)
        return notification

    async def mark_email_sent(self, notification: UserNotification) -> None:
        notification.email_sent_at = datetime.now(UTC)
        await self._db.flush()
