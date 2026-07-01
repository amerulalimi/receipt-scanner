from redis.asyncio import Redis



from app.core.config import settings

from app.core.exceptions import AppError

from app.core.rate_limiter import RATE_LIMIT_MESSAGE, enforce_rate_limit





async def check_rate_limit(

    redis: Redis,

    *,

    key: str,

    max_requests: int | None = None,

    window_seconds: int | None = None,

) -> None:

    limit = max_requests if max_requests is not None else settings.auth_rate_limit_max
    window = window_seconds or settings.auth_rate_limit_window_seconds

    if limit <= 0:
        return

    count = await redis.incr(key)

    if count == 1:

        await redis.expire(key, window)



    if count > limit:

        raise AppError(

            message=RATE_LIMIT_MESSAGE,

            code="RATE_LIMITED",

            status_code=429,

        )

