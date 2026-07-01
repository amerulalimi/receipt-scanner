from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import (
    RELIEF_LIMITS_CACHE_KEY,
    RELIEF_LIMITS_TTL,
    get_cached,
    invalidate_cache,
    set_cached,
)
from app.models.relief_limit import ReliefLimit
from app.repositories.relief_limit import ReliefLimitRepository


def _serialize_limits(items: list[ReliefLimit]) -> dict[str, Any]:
    return {
        "items": [
            {
                "id": str(item.id),
                "category": item.category,
                "be_seksyen": item.be_seksyen,
                "limit_amount": str(item.limit_amount),
                "description_en": item.description_en,
                "description_my": item.description_my,
                "sort_order": item.sort_order,
                "is_active": item.is_active,
            }
            for item in items
        ],
    }


def _deserialize_limits(payload: dict[str, Any]) -> list[ReliefLimit]:
    items: list[ReliefLimit] = []
    for row in payload.get("items", []):
        items.append(
            ReliefLimit(
                id=uuid.UUID(row["id"]),
                category=row["category"],
                be_seksyen=row.get("be_seksyen"),
                limit_amount=Decimal(row["limit_amount"]),
                description_en=row.get("description_en"),
                description_my=row.get("description_my"),
                sort_order=int(row.get("sort_order", 0)),
                is_active=bool(row.get("is_active", True)),
            ),
        )
    return items


async def get_active_relief_limits(
    db: AsyncSession,
    redis: Redis | None = None,
) -> list[ReliefLimit]:
    if redis is not None:
        cached = await get_cached(redis, RELIEF_LIMITS_CACHE_KEY)
        if cached is not None:
            return _deserialize_limits(cached)

    repo = ReliefLimitRepository(db)
    items = await repo.list_active()

    if redis is not None:
        await set_cached(
            redis,
            RELIEF_LIMITS_CACHE_KEY,
            _serialize_limits(items),
            RELIEF_LIMITS_TTL,
        )

    return items


async def invalidate_relief_limits_cache(redis: Redis) -> None:
    await invalidate_cache(redis, RELIEF_LIMITS_CACHE_KEY)
