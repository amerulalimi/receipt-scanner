"""Migrate deprecated model and re-queue unprocessed receipts."""
import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.services.job_queue import create_worker_redis
from app.services.receipt_requeue import migrate_deprecated_vision_model, requeue_unprocessed_receipts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    redis = create_worker_redis()
    await redis.ping()

    async with AsyncSessionLocal() as db:
        migrated = await migrate_deprecated_vision_model(db)
        if migrated:
            logger.info("Updated vision model to %s", migrated)

        count = await requeue_unprocessed_receipts(db, redis)
        await db.commit()
        logger.info("Re-queued %s receipt(s)", count)

    await redis.aclose()


if __name__ == "__main__":
    asyncio.run(main())
