from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import AppError


async def check_rate_limit(
    redis: Redis,
    *,
    key: str,
    max_requests: int | None = None,
    window_seconds: int | None = None,
) -> None:
    limit = max_requests or settings.auth_rate_limit_max
    window = window_seconds or settings.auth_rate_limit_window_seconds

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, window)

    if count > limit:
        raise AppError(
            message="Terlalu banyak percubaan. Sila cuba lagi kemudian.",
            code="RATE_LIMITED",
            status_code=429,
        )
