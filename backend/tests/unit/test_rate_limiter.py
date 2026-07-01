import pytest
import fakeredis.aioredis

from app.core.exceptions import AppError
from app.core.rate_limiter import enforce_rate_limit


@pytest.fixture
async def redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest.mark.asyncio
async def test_disabled_when_max_requests_zero(redis):
    await enforce_rate_limit(
        redis,
        key_prefix="test",
        identifier="user-disabled",
        max_requests=0,
        window_seconds=60,
    )
    await redis.set("rl:test:user-disabled", "999")
    await enforce_rate_limit(
        redis,
        key_prefix="test",
        identifier="user-disabled",
        max_requests=0,
        window_seconds=60,
    )


@pytest.mark.asyncio
async def test_first_request_allowed(redis):
    await enforce_rate_limit(
        redis,
        key_prefix="test",
        identifier="user-1",
        max_requests=5,
        window_seconds=60,
    )


@pytest.mark.asyncio
async def test_under_limit_allowed(redis):
    key = "rl:test:user-2"
    await redis.set(key, "3")
    await redis.expire(key, 60)
    await enforce_rate_limit(
        redis,
        key_prefix="test",
        identifier="user-2",
        max_requests=5,
        window_seconds=60,
    )


@pytest.mark.asyncio
async def test_at_limit_blocked(redis):
    key = "rl:test:user-3"
    await redis.set(key, "5")
    await redis.expire(key, 60)
    with pytest.raises(AppError) as exc:
        await enforce_rate_limit(
            redis,
            key_prefix="test",
            identifier="user-3",
            max_requests=5,
            window_seconds=60,
        )
    assert exc.value.status_code == 429
    assert exc.value.code == "RATE_LIMITED"


@pytest.mark.asyncio
async def test_window_reset(redis):
    key = "rl:test:user-4"
    await redis.set(key, "5")
    await redis.expire(key, 1)
    import asyncio

    await asyncio.sleep(1.1)
    await enforce_rate_limit(
        redis,
        key_prefix="test",
        identifier="user-4",
        max_requests=5,
        window_seconds=60,
    )


@pytest.mark.asyncio
async def test_different_keys_independent(redis):
    key_a = "rl:test:key-a"
    await redis.set(key_a, "5")
    await redis.expire(key_a, 60)

    with pytest.raises(AppError):
        await enforce_rate_limit(
            redis,
            key_prefix="test",
            identifier="key-a",
            max_requests=5,
            window_seconds=60,
        )

    await enforce_rate_limit(
        redis,
        key_prefix="test",
        identifier="key-b",
        max_requests=5,
        window_seconds=60,
    )
