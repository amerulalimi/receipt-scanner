import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.models.user_notification import UserNotification
from app.repositories.user_notification import UserNotificationRepository
from app.schemas.notifications import NotificationPreferenceUpdateRequest
from app.services.notifications import NotificationService
from app.services.reminders import ReminderEngine
from tests.conftest import seed_relief_limits, seed_user


@pytest.mark.asyncio
async def test_get_notifications_empty(db_session, test_user):
    service = NotificationService(db_session)
    with patch.object(
        ReminderEngine,
        "evaluate",
        new_callable=AsyncMock,
        return_value=[],
    ):
        result = await service.sync_and_list(test_user)
    assert result.items == []


@pytest.mark.asyncio
async def test_generate_reminder_zero_receipts(db_session):
    await seed_relief_limits(db_session)
    user = await seed_user(
        db_session,
        email="zero-med@example.com",
        tax_year=2026,
    )
    engine = ReminderEngine(db_session)
    limits = await engine._limits.list_active()
    candidates = engine._year_end_zero_category_reminders(
        tax_year=2026,
        today=date(2026, 12, 15),
        limits=limits,
        summary_by_category={},
        receipt_counts={},
    )

    assert len(candidates) >= 1
    assert any(item.severity == "warning" for item in candidates)

    service = NotificationService(db_session)
    for candidate in candidates:
        await service._notifications.upsert(
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

    result = await service._notifications.list_active_for_user(user.id)
    assert any(item.severity == "warning" for item in result)


@pytest.mark.asyncio
async def test_generate_reminder_dedup(db_session):
    await seed_relief_limits(db_session)
    user = await seed_user(
        db_session,
        email="dedup@example.com",
        tax_bracket=None,
        full_name=None,
    )
    service = NotificationService(db_session)

    first = await service.sync_and_list(user)
    second = await service.sync_and_list(user)

    assert first.total >= 1
    assert second.total == first.total


@pytest.mark.asyncio
async def test_dismiss_notification(db_session, test_user):
    repo = UserNotificationRepository(db_session)
    notification = await repo.upsert(
        user_id=test_user.id,
        reminder_key="test-dismiss",
        type="test",
        severity="info",
        title_my="Tajuk",
        title_en="Title",
        message_my="Mesej",
        message_en="Message",
        action_href=None,
        expires_at=None,
    )
    service = NotificationService(db_session)

    await service.dismiss(test_user, notification.id)
    await db_session.refresh(notification)

    assert notification.dismissed_at is not None


@pytest.mark.asyncio
async def test_update_preferences(db_session, test_user):
    service = NotificationService(db_session)
    updated = await service.update_preferences(
        test_user,
        NotificationPreferenceUpdateRequest(email_enabled=False),
    )

    assert updated.email_enabled is False


@pytest.mark.asyncio
async def test_expired_notifications_excluded(db_session, test_user):
    db_session.add(
        UserNotification(
            id=uuid.uuid4(),
            user_id=test_user.id,
            reminder_key="expired-test",
            type="test",
            severity="info",
            title_my="Lama",
            title_en="Old",
            message_my="Tamat",
            message_en="Expired",
            created_at=datetime.now(UTC) - timedelta(days=2),
            expires_at=datetime.now(UTC) - timedelta(days=1),
        ),
    )
    await db_session.commit()

    repo = UserNotificationRepository(db_session)
    active = await repo.list_active_for_user(test_user.id)

    assert all(item.reminder_key != "expired-test" for item in active)
