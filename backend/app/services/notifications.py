from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.user import User
from app.repositories.notification_preference import NotificationPreferenceRepository
from app.repositories.user import UserRepository
from app.repositories.user_notification import UserNotificationRepository
from app.schemas.notifications import (
    NotificationItem,
    NotificationListResponse,
    NotificationPreferenceData,
    NotificationPreferenceUpdateRequest,
)
from app.services.email import send_monthly_digest_email, send_reminder_email
from app.services.reminders import ReminderEngine


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._preferences = NotificationPreferenceRepository(db)
        self._notifications = UserNotificationRepository(db)
        self._users = UserRepository(db)
        self._reminders = ReminderEngine(db)

    async def get_preferences(self, user: User) -> NotificationPreferenceData:
        preference = await self._preferences.get_or_create(user.id)
        return NotificationPreferenceData(
            email_enabled=preference.email_enabled,
            in_app_enabled=preference.in_app_enabled,
            digest_frequency=preference.digest_frequency,  # type: ignore[arg-type]
        )

    async def update_preferences(
        self,
        user: User,
        payload: NotificationPreferenceUpdateRequest,
    ) -> NotificationPreferenceData:
        preference = await self._preferences.get_or_create(user.id)
        updated = await self._preferences.update(
            preference,
            email_enabled=payload.email_enabled,
            in_app_enabled=payload.in_app_enabled,
            digest_frequency=payload.digest_frequency,
        )
        return NotificationPreferenceData(
            email_enabled=updated.email_enabled,
            in_app_enabled=updated.in_app_enabled,
            digest_frequency=updated.digest_frequency,  # type: ignore[arg-type]
        )

    async def sync_and_list(self, user: User) -> NotificationListResponse:
        preference = await self._preferences.get_or_create(user.id)

        if preference.in_app_enabled:
            candidates = await self._reminders.evaluate(user)
            for candidate in candidates:
                await self._notifications.upsert(
                    user_id=user.id,
                    reminder_key=candidate.reminder_key,
                    type=candidate.type,
                    severity=candidate.severity,
                    title_my=candidate.title_my,
                    title_en=candidate.title_en,
                    message_my=candidate.message_my,
                    message_en=candidate.message_en,
                    action_href=candidate.action_href,
                    expires_at=candidate.expires_at,
                )

        active = await self._notifications.list_active_for_user(user.id)
        items = [
            NotificationItem(
                id=item.id,
                type=item.type,
                severity=item.severity,  # type: ignore[arg-type]
                title_my=item.title_my,
                title_en=item.title_en,
                message_my=item.message_my,
                message_en=item.message_en,
                action_href=item.action_href,
                created_at=item.created_at,
            )
            for item in active
        ]
        return NotificationListResponse(items=items, total=len(items))

    async def dismiss(self, user: User, notification_id: uuid.UUID) -> None:
        notification = await self._notifications.get_by_id_for_user(
            notification_id,
            user.id,
        )
        if notification is None:
            raise AppError(
                message="Notifikasi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        await self._notifications.dismiss(notification)

    async def send_due_monthly_digests(self) -> int:
        now = datetime.now(UTC)
        month_start = datetime(now.year, now.month, 1, tzinfo=UTC)
        user_ids = await self._preferences.list_users_due_for_digest(
            month_start=month_start,
        )

        sent_count = 0
        for user_id in user_ids:
            user = await self._users.get_by_id(user_id)
            if user is None or not user.is_active or not user.email_verified:
                continue

            preference = await self._preferences.get(user_id)
            if preference is None or not preference.email_enabled:
                continue

            body_my, body_en = await self._reminders.build_monthly_digest_email(user)
            await send_monthly_digest_email(
                email=user.email,
                body_my=body_my,
                body_en=body_en,
            )
            await self._preferences.update(
                preference,
                last_monthly_digest_at=now,
            )
            sent_count += 1

        return sent_count

    async def send_email_for_active_reminders(self, user: User) -> int:
        preference = await self._preferences.get_or_create(user.id)
        if not preference.email_enabled:
            return 0

        candidates = await self._reminders.evaluate(user)
        sent = 0

        for candidate in candidates:
            if candidate.type not in {"year_end_zero_category", "calendar_nudge"}:
                continue

            existing = await self._notifications.get_by_key(
                user_id=user.id,
                reminder_key=candidate.reminder_key,
            )
            if existing is not None and existing.email_sent_at is not None:
                continue

            await send_reminder_email(
                email=user.email,
                title_my=candidate.title_my,
                title_en=candidate.title_en,
                message_my=candidate.message_my,
                message_en=candidate.message_en,
            )

            notification = await self._notifications.upsert(
                user_id=user.id,
                reminder_key=candidate.reminder_key,
                type=candidate.type,
                severity=candidate.severity,
                title_my=candidate.title_my,
                title_en=candidate.title_en,
                message_my=candidate.message_my,
                message_en=candidate.message_en,
                action_href=candidate.action_href,
                expires_at=candidate.expires_at,
            )
            await self._notifications.mark_email_sent(notification)
            sent += 1

        return sent
