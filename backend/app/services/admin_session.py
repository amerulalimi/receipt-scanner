from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

ADMIN_SESSION_PREFIX = "admin_sess:"
ADMIN_SESSIONS_PREFIX = "admin_user_sessions:"
ADMIN_SESSION_TTL = settings.admin_session_ttl_seconds
ADMIN_SESSION_RENEW_WINDOW = 1800


def _session_key(session_id: str) -> str:
    return f"{ADMIN_SESSION_PREFIX}{session_id}"


def _admin_sessions_key(admin_id: uuid.UUID) -> str:
    return f"{ADMIN_SESSIONS_PREFIX}{admin_id}"


async def create_admin_session(
    redis: Redis,
    *,
    admin_id: uuid.UUID,
    email: str,
    ip: str,
    user_agent: str,
) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    session_data: dict[str, Any] = {
        "session_id": session_id,
        "admin_id": str(admin_id),
        "email": email,
        "created_at": now,
        "last_active": now,
        "ip": ip,
        "user_agent": user_agent,
    }

    pipe = redis.pipeline()
    pipe.setex(
        _session_key(session_id),
        ADMIN_SESSION_TTL,
        json.dumps(session_data),
    )
    pipe.sadd(_admin_sessions_key(admin_id), session_id)
    await pipe.execute()

    await _enforce_session_limit(redis, admin_id)
    return session_id


async def _enforce_session_limit(redis: Redis, admin_id: uuid.UUID) -> None:
    admin_key = _admin_sessions_key(admin_id)
    session_ids = await redis.smembers(admin_key)

    if len(session_ids) <= settings.max_admin_sessions_per_admin:
        return

    sessions: list[tuple[str, datetime]] = []
    for sid in session_ids:
        raw = await redis.get(_session_key(sid))
        if raw is None:
            await redis.srem(admin_key, sid)
            continue
        data = json.loads(raw)
        created_at = datetime.fromisoformat(data["created_at"])
        sessions.append((sid, created_at))

    sessions.sort(
        key=lambda item: item[1].replace(tzinfo=UTC) if item[1].tzinfo is None else item[1],
    )
    excess = len(sessions) - settings.max_admin_sessions_per_admin
    for sid, _ in sessions[:excess]:
        await delete_admin_session(redis, admin_id=admin_id, session_id=sid)


async def delete_admin_session(
    redis: Redis,
    *,
    admin_id: uuid.UUID,
    session_id: str,
) -> None:
    pipe = redis.pipeline()
    pipe.delete(_session_key(session_id))
    pipe.srem(_admin_sessions_key(admin_id), session_id)
    await pipe.execute()


async def get_admin_session(redis: Redis, session_id: str) -> dict[str, Any] | None:
    raw = await redis.get(_session_key(session_id))
    if raw is None:
        return None

    session_data: dict[str, Any] = json.loads(raw)
    last_active = datetime.fromisoformat(session_data["last_active"])
    now = datetime.now(UTC)
    renew_threshold = now - timedelta(seconds=ADMIN_SESSION_RENEW_WINDOW)

    session_data["last_active"] = now.isoformat()

    if last_active >= renew_threshold:
        await redis.setex(
            _session_key(session_id),
            ADMIN_SESSION_TTL,
            json.dumps(session_data),
        )
    else:
        ttl = await redis.ttl(_session_key(session_id))
        if ttl > 0:
            await redis.setex(
                _session_key(session_id),
                ttl,
                json.dumps(session_data),
            )

    return session_data


async def touch_admin_session(
    redis: Redis,
    session_id: str,
    session_data: dict[str, Any],
) -> None:
    session_data["last_active"] = datetime.now(UTC).isoformat()
    await redis.setex(
        _session_key(session_id),
        ADMIN_SESSION_TTL,
        json.dumps(session_data),
    )
