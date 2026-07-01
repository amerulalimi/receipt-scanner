from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.deps import get_client_ip, get_redis_client, get_session_data_dep
from app.core.config import settings
from app.core.exceptions import AppError

RATE_LIMIT_MESSAGE = "Terlalu banyak permintaan. Cuba lagi sebentar."


def effective_rate_limit(limit: int) -> int:
    """Return 0 when rate limiting is globally disabled (auth_rate_limit_max <= 0)."""
    if settings.auth_rate_limit_max <= 0:
        return 0
    return limit


def _rate_limit_key(key_prefix: str, identifier: str) -> str:
    return f"rl:{key_prefix}:{identifier}"


async def enforce_rate_limit(
    redis: Redis,
    *,
    key_prefix: str,
    identifier: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    if max_requests <= 0:
        return

    key = _rate_limit_key(key_prefix, identifier)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window_seconds)

    if count > max_requests:
        raise AppError(
            message=RATE_LIMIT_MESSAGE,
            code="RATE_LIMITED",
            status_code=429,
        )


class RateLimiter:
    """FastAPI dependency factory for Redis-backed rate limiting."""

    def __init__(
        self,
        key_prefix: str,
        max_requests: int,
        window_seconds: int,
        *,
        identifier: Callable[..., str] | None = None,
    ) -> None:
        self.key_prefix = key_prefix
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._identifier = identifier

    async def __call__(
        self,
        request: Request,
        redis: Redis = Depends(get_redis_client),
    ) -> None:
        if self._identifier is not None:
            ident = self._identifier(request)
        else:
            ident = get_client_ip(request)

        await enforce_rate_limit(
            redis,
            key_prefix=self.key_prefix,
            identifier=ident,
            max_requests=self.max_requests,
            window_seconds=self.window_seconds,
        )


def _user_id_from_session(session_data: dict) -> str:
    return str(session_data["user_id"])


def user_rate_limiter(
    key_prefix: str,
    max_requests: int,
    window_seconds: int,
) -> Callable[..., None]:
    async def _dependency(
        session_data: Annotated[dict, Depends(get_session_data_dep)],
        redis: Redis = Depends(get_redis_client),
    ) -> None:
        await enforce_rate_limit(
            redis,
            key_prefix=key_prefix,
            identifier=str(session_data["user_id"]),
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

    return _dependency
