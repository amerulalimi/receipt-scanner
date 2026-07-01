from __future__ import annotations

import json
from typing import Any

from redis.asyncio import Redis

RELIEF_LIMITS_CACHE_KEY = "cache:relief_limits"
RELIEF_LIMITS_TTL = 3600


async def get_cached(redis: Redis, key: str) -> dict | None:
    raw = await redis.get(key)
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    return None


async def set_cached(
    redis: Redis,
    key: str,
    value: dict[str, Any],
    ttl: int,
) -> None:
    await redis.set(key, json.dumps(value), ex=ttl)


async def invalidate_cache(redis: Redis, key: str) -> None:
    await redis.delete(key)
