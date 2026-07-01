import pytest
import fakeredis.aioredis
from unittest.mock import AsyncMock

from app.core.cache import get_cached, invalidate_cache, set_cached
from app.services.relief_limits_cache import get_active_relief_limits


@pytest.fixture
async def redis():
    client = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.flushall()
    await client.aclose()


@pytest.mark.asyncio
async def test_set_and_get_cached(redis):
    await set_cached(redis, "test:key", {"hello": "world"}, 60)
    result = await get_cached(redis, "test:key")
    assert result == {"hello": "world"}


@pytest.mark.asyncio
async def test_cache_miss(redis):
    assert await get_cached(redis, "missing") is None


@pytest.mark.asyncio
async def test_invalidate_cache(redis):
    await set_cached(redis, "test:key", {"a": 1}, 60)
    await invalidate_cache(redis, "test:key")
    assert await get_cached(redis, "test:key") is None


@pytest.mark.asyncio
async def test_relief_limits_cached(redis, db_session, monkeypatch):
    list_active = AsyncMock(return_value=[])
    monkeypatch.setattr(
        "app.services.relief_limits_cache.ReliefLimitRepository.list_active",
        list_active,
    )
    await get_active_relief_limits(db_session, redis)
    await get_active_relief_limits(db_session, redis)

    assert list_active.await_count == 1
