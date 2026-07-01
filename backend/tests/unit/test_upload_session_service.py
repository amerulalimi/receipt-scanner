import pytest

from app.core.config import settings
from app.core.exceptions import AppError
from app.services.upload_session import QR_PREFIX, UploadSessionService


@pytest.mark.unit
async def test_create_qr_session(db_session, fake_redis, test_user):
    service = UploadSessionService(db_session, fake_redis)
    result = await service.create_session(
        test_user,
        desktop_session_id="desktop-session-1",
        tax_year=2025,
    )

    assert result.token
    cached = await fake_redis.get(f"{QR_PREFIX}{result.token}")
    assert cached is not None

    from app.repositories.upload_session import UploadSessionRepository

    row = await UploadSessionRepository(db_session).get_by_token(result.token)
    assert row is not None
    assert row.user_id == test_user.id


@pytest.mark.unit
async def test_validate_qr_session_valid(db_session, fake_redis, test_user):
    service = UploadSessionService(db_session, fake_redis)
    created = await service.create_session(
        test_user,
        desktop_session_id="desktop-session-1",
    )

    validated = await service.validate_token(created.token)
    assert validated.valid is True
    assert validated.uploads_so_far == 0
    assert validated.inactivity_remaining > 0


@pytest.mark.unit
async def test_validate_qr_session_expired(db_session, fake_redis, test_user):
    service = UploadSessionService(db_session, fake_redis)
    created = await service.create_session(
        test_user,
        desktop_session_id="desktop-session-1",
    )

    from app.repositories.upload_session import UploadSessionRepository

    session = await UploadSessionRepository(db_session).get_by_token(created.token)
    assert session is not None
    session.status = "expired"
    await UploadSessionRepository(db_session).update(session)
    await db_session.commit()

    with pytest.raises(AppError) as exc:
        await service.validate_token(created.token)
    assert exc.value.code == "SESSION_EXPIRED"
    assert exc.value.status_code == 401


@pytest.mark.unit
async def test_record_upload(db_session, fake_redis, test_user):
    service = UploadSessionService(db_session, fake_redis)
    created = await service.create_session(
        test_user,
        desktop_session_id="desktop-session-1",
    )

    ttl_before = await fake_redis.ttl(f"{QR_PREFIX}{created.token}")

    from app.repositories.upload_session import UploadSessionRepository

    session = await UploadSessionRepository(db_session).get_by_token(created.token)
    assert session is not None
    session.uploads_count += 1
    session.last_upload_at = session.created_at
    await UploadSessionRepository(db_session).update(session)
    await db_session.commit()
    await service._refresh_qr_cache(session)

    ttl_after = await fake_redis.ttl(f"{QR_PREFIX}{created.token}")
    assert ttl_after >= ttl_before


@pytest.mark.unit
async def test_close_qr_session(db_session, fake_redis, test_user):
    service = UploadSessionService(db_session, fake_redis)
    created = await service.create_session(
        test_user,
        desktop_session_id="desktop-session-1",
    )

    pubsub = fake_redis.pubsub()
    await pubsub.subscribe(settings.ws_events_channel)

    closed = await service.close_session(created.token)
    assert closed.uploads_count == 0

    cached = await fake_redis.get(f"{QR_PREFIX}{created.token}")
    assert cached is None

    message = None
    for _ in range(5):
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.2)
        if message is not None and message.get("type") == "message":
            break

    assert message is not None
    assert "session_closed" in message["data"]
    await pubsub.aclose()


@pytest.mark.unit
async def test_inactivity_warning_triggered(db_session, fake_redis, test_user):
    service = UploadSessionService(db_session, fake_redis)
    created = await service.create_session(
        test_user,
        desktop_session_id="desktop-session-1",
    )

    await fake_redis.expire(f"{QR_PREFIX}{created.token}", 90)
    remaining = await service.check_inactivity_warning(created.token)
    assert remaining == 90
