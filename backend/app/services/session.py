from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings

SESSION_PREFIX = "sess:"
USER_SESSIONS_PREFIX = "user_sessions:"
SESSION_TTL = settings.session_ttl_seconds
SESSION_RENEW_WINDOW = 1800
MAX_SESSIONS_PER_USER = settings.max_sessions_per_user


def _session_key(session_id: str) -> str:
    return f"{SESSION_PREFIX}{session_id}"


def _user_sessions_key(user_id: uuid.UUID) -> str:
    return f"{USER_SESSIONS_PREFIX}{user_id}"


async def create_session(
    redis: Redis,
    *,
    user_id: uuid.UUID,
    role: str,
    org_id: uuid.UUID | None,
    active_context: str,
    email: str,
    ip: str,
    user_agent: str,
) -> str:
    session_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    session_data: dict[str, Any] = {
        "session_id": session_id,
        "user_id": str(user_id),
        "role": role,
        "org_id": str(org_id) if org_id else None,
        "active_context": active_context,
        "email": email,
        "created_at": now,
        "last_active": now,
        "ip": ip,
        "user_agent": user_agent,
    }

    pipe = redis.pipeline()
    pipe.setex(
        _session_key(session_id),
        SESSION_TTL,
        json.dumps(session_data),
    )
    pipe.sadd(_user_sessions_key(user_id), session_id)
    await pipe.execute()

    await _enforce_session_limit(redis, user_id)
    return session_id


async def _enforce_session_limit(redis: Redis, user_id: uuid.UUID) -> None:
    user_key = _user_sessions_key(user_id)
    session_ids = await redis.smembers(user_key)

    if len(session_ids) <= settings.max_sessions_per_user:
        return

    sessions: list[tuple[str, datetime]] = []
    for sid in session_ids:
        raw = await redis.get(_session_key(sid))
        if raw is None:
            await redis.srem(user_key, sid)
            continue
        data = json.loads(raw)
        created_at = datetime.fromisoformat(data["created_at"])
        sessions.append((sid, created_at))

    sessions.sort(key=lambda item: item[1].replace(tzinfo=UTC) if item[1].tzinfo is None else item[1])
    excess = len(sessions) - settings.max_sessions_per_user
    for sid, _ in sessions[:excess]:
        await delete_session(redis, user_id=user_id, session_id=sid)


async def delete_session(
    redis: Redis,
    *,
    user_id: uuid.UUID,
    session_id: str,
) -> None:
    pipe = redis.pipeline()
    pipe.delete(_session_key(session_id))
    pipe.srem(_user_sessions_key(user_id), session_id)
    await pipe.execute()


async def get_session(redis: Redis, session_id: str) -> dict[str, Any] | None:
    raw = await redis.get(_session_key(session_id))
    if raw is None:
        return None

    session_data: dict[str, Any] = json.loads(raw)
    last_active = datetime.fromisoformat(session_data["last_active"])
    now = datetime.now(UTC)
    renew_threshold = now - timedelta(seconds=SESSION_RENEW_WINDOW)

    session_data["last_active"] = now.isoformat()

    if last_active >= renew_threshold:
        await redis.setex(
            _session_key(session_id),
            SESSION_TTL,
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


async def get_session_data(redis: Redis, session_id: str) -> dict[str, Any] | None:
    """Backward-compatible alias for get_session."""
    return await get_session(redis, session_id)


async def touch_session(redis: Redis, session_id: str, session_data: dict[str, Any]) -> None:
    """Force session TTL renewal (used by refresh endpoint)."""
    session_data["last_active"] = datetime.now(UTC).isoformat()
    await redis.setex(
        _session_key(session_id),
        SESSION_TTL,
        json.dumps(session_data),
    )


async def get_user_sessions(
    redis: Redis,
    *,
    user_id: uuid.UUID,
    current_session_id: str | None = None,
) -> list[dict[str, Any]]:
    return await list_user_sessions(
        redis,
        user_id=user_id,
        current_session_id=current_session_id,
    )


async def list_user_sessions(
    redis: Redis,
    *,
    user_id: uuid.UUID,
    current_session_id: str | None,
) -> list[dict[str, Any]]:
    session_ids = await redis.smembers(_user_sessions_key(user_id))
    sessions: list[dict[str, Any]] = []

    for sid in session_ids:
        raw = await redis.get(_session_key(sid))
        if raw is None:
            await redis.srem(_user_sessions_key(user_id), sid)
            continue
        data = json.loads(raw)
        data["is_current"] = sid == current_session_id
        sessions.append(data)

    sessions.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return sessions
