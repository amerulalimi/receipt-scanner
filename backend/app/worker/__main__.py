from app.worker.bootstrap import validate_worker_runtime

validate_worker_runtime()

import asyncio
import logging

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.storage import ensure_upload_root
from app.services.job_queue import create_worker_redis, dequeue_receipt_job
from app.services.receipt_processor import ReceiptProcessor

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    ensure_upload_root()
    redis = create_worker_redis()
    await redis.ping()
    logger.info("Worker started — queue: %s", settings.receipt_queue_key)

    try:
        while True:
            job = await dequeue_receipt_job(redis)
            if job is None:
                continue

            logger.info("Processing receipt job %s", job.receipt_id)
            async with AsyncSessionLocal() as db:
                try:
                    processor = ReceiptProcessor(db, redis)
                    await processor.process(job)
                    await db.commit()
                    logger.info("Completed receipt job %s", job.receipt_id)
                except Exception:
                    logger.exception("Unhandled error for receipt job %s", job.receipt_id)
                    await db.rollback()
    finally:
        await redis.aclose()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
