from __future__ import annotations

import logging
import secrets
import uuid

from redis.asyncio import Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

VERIFY_PREFIX = "email_verify:"


async def create_verification_token(redis: Redis, user_id: uuid.UUID) -> str:
    token = secrets.token_urlsafe(32)
    await redis.setex(
        f"{VERIFY_PREFIX}{token}",
        settings.email_verification_ttl_seconds,
        str(user_id),
    )
    return token


async def consume_verification_token(
    redis: Redis,
    token: str,
) -> uuid.UUID | None:
    key = f"{VERIFY_PREFIX}{token}"
    raw_user_id = await redis.get(key)
    if raw_user_id is None:
        return None

    await redis.delete(key)
    return uuid.UUID(raw_user_id)
