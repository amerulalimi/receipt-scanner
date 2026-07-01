"""Standalone receipt worker entry helpers (used by app.worker and tests)."""

from __future__ import annotations

import asyncio
import logging

from app.core.config import settings
from app.core.storage import ensure_upload_root
from app.core.startup import touch_worker_heartbeat
from app.services.job_queue import create_worker_redis, dequeue_receipt_job, process_receipt_job

logger = logging.getLogger(__name__)


async def run_worker() -> None:
    ensure_upload_root()
    redis = create_worker_redis()
    await redis.ping()
    logger.info("Worker started — queue: %s", settings.receipt_queue_key)

    try:
        while True:
            await touch_worker_heartbeat(redis)
            job = await dequeue_receipt_job(redis)
            if job is None:
                continue
            await process_receipt_job(redis, job)
    finally:
        await redis.aclose()
