import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.system_config import SystemConfigRepository
from app.services.job_queue import enqueue_receipt_job

logger = logging.getLogger(__name__)


async def migrate_deprecated_vision_model(db: AsyncSession) -> str | None:
    from app.core.secret_keys import DEPRECATED_VISION_MODELS

    config = SystemConfigRepository(db)
    item = await config.get_by_key("openrouter_vision_model")
    if item is None:
        return None

    replacement = DEPRECATED_VISION_MODELS.get(item.value)
    if replacement is None:
        return None

    old_value = item.value
    item.value = replacement
    await db.flush()
    logger.info("Migrated vision model %s -> %s", old_value, replacement)
    return replacement


async def requeue_unprocessed_receipts(db: AsyncSession, redis: Redis) -> int:
    from sqlalchemy import select

    from app.models.receipt import Receipt

    result = await db.execute(
        select(Receipt)
        .where(
            Receipt.deleted_at.is_(None),
            Receipt.merchant_name.is_(None),
            Receipt.category == "semak_manual",
        )
        .order_by(Receipt.created_at.asc()),
    )
    receipts = list(result.scalars().all())
    count = 0
    for receipt in receipts:
        await enqueue_receipt_job(
            redis,
            receipt_id=receipt.id,
            user_id=receipt.user_id,
        )
        count += 1
    return count
