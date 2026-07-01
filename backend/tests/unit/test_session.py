import json
import uuid
from datetime import UTC, datetime, timedelta

import fakeredis.aioredis
import pytest

from app.core.config import settings
from app.services import session as session_module
from app.services.session import (
    SESSION_PREFIX,
    SESSION_TTL,
    create_session,
    delete_session,
    get_session,
)


@pytest.fixture
async def redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest.mark.unit
async def test_create_session(redis):
    user_id = uuid.uuid4()
    session_id = await create_session(
        redis,
        user_id=user_id,
        role="individual",
        org_id=None,
        email="user@example.com",
        ip="127.0.0.1",
        user_agent="pytest",
    )

    raw = await redis.get(f"{SESSION_PREFIX}{session_id}")
    assert raw is not None
    data = json.loads(raw)
    assert data["email"] == "user@example.com"
    ttl = await redis.ttl(f"{SESSION_PREFIX}{session_id}")
    assert 0 < ttl <= SESSION_TTL


@pytest.mark.unit
async def test_get_session_valid(redis):
    user_id = uuid.uuid4()
    session_id = await create_session(
        redis,
        user_id=user_id,
        role="individual",
        org_id=None,
        email="user@example.com",
        ip="127.0.0.1",
        user_agent="pytest",
    )

    data = await get_session(redis, session_id)
    assert data is not None
    assert data["session_id"] == session_id


@pytest.mark.unit
async def test_get_session_expired(redis):
    data = await get_session(redis, "nonexistent-session-id")
    assert data is None


@pytest.mark.unit
async def test_delete_session(redis):
    user_id = uuid.uuid4()
    session_id = await create_session(
        redis,
        user_id=user_id,
        role="individual",
        org_id=None,
        email="user@example.com",
        ip="127.0.0.1",
        user_agent="pytest",
    )

    await delete_session(redis, user_id=user_id, session_id=session_id)
    assert await redis.get(f"{SESSION_PREFIX}{session_id}") is None


@pytest.mark.unit
async def test_max_sessions_enforced(redis, monkeypatch):
    monkeypatch.setattr(settings, "max_sessions_per_user", 2)

    user_id = uuid.uuid4()
    ids = []
    for _ in range(3):
        sid = await create_session(
            redis,
            user_id=user_id,
            role="individual",
            org_id=None,
            email="user@example.com",
            ip="127.0.0.1",
            user_agent="pytest",
        )
        ids.append(sid)

    active = await redis.smembers(f"user_sessions:{user_id}")
    assert len(active) == 2

    remaining = 0
    for sid in ids:
        if await redis.get(f"{SESSION_PREFIX}{sid}") is not None:
            remaining += 1
    assert remaining == 2
