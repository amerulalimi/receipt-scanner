from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import UTC, datetime

from redis.asyncio import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.secret_keys import CONFIG_DEFAULTS, resolve_vision_model
from app.repositories.system_config import SystemConfigRepository
from app.schemas.receipt_job import ReceiptJobPayload, WsEventMessage
from app.services.secret_settings import SecretSettingsService

logger = logging.getLogger(__name__)

JOB_STATUS_TTL_SECONDS = 86400


def create_worker_redis() -> Redis:
    """Redis client for blocking BRPOP — socket timeout must exceed poll timeout."""
    poll_timeout = settings.worker_poll_timeout
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=poll_timeout + 10,
    )


def _job_status_key(job_id: str) -> str:
    return f"job:{job_id}"


async def is_processing_enabled(db: AsyncSession) -> bool:
    config = SystemConfigRepository(db)
    item = await config.get_by_key("receipt_processing_enabled")
    value = item.value if item else CONFIG_DEFAULTS["receipt_processing_enabled"]
    return value.lower() == "true"


async def enqueue_receipt_job(
    redis: Redis,
    *,
    receipt_id: uuid.UUID,
    user_id: uuid.UUID,
    upload_session_token: str | None = None,
) -> str:
    job_id = str(uuid.uuid4())
    payload = ReceiptJobPayload(
        job_id=job_id,
        receipt_id=receipt_id,
        user_id=user_id,
        upload_session_token=upload_session_token,
    )
    await redis.lpush(settings.receipt_queue_key, payload.model_dump_json())
    status = {
        "status": "queued",
        "receipt_id": str(receipt_id),
        "created_at": datetime.now(UTC).isoformat(),
    }
    await redis.set(
        _job_status_key(job_id),
        json.dumps(status),
        ex=JOB_STATUS_TTL_SECONDS,
    )
    logger.info("Enqueued receipt job %s for receipt %s", job_id, receipt_id)
    return job_id


async def get_job_status(redis: Redis, job_id: str) -> dict | None:
    raw = await redis.get(_job_status_key(job_id))
    if raw is None:
        return None
    return json.loads(raw)


async def update_job_status(
    redis: Redis,
    job_id: str,
    status: str,
    **extra: object,
) -> None:
    existing = await get_job_status(redis, job_id) or {}
    existing["status"] = status
    existing.update(extra)
    await redis.set(
        _job_status_key(job_id),
        json.dumps(existing),
        ex=JOB_STATUS_TTL_SECONDS,
    )


async def try_dequeue_receipt_job(redis: Redis) -> ReceiptJobPayload | None:
    raw = await redis.rpop(settings.receipt_queue_key)
    if raw is None:
        return None
    return ReceiptJobPayload.model_validate_json(raw)


async def dequeue_receipt_job(redis: Redis) -> ReceiptJobPayload | None:
    try:
        result = await redis.brpop(
            settings.receipt_queue_key,
            timeout=settings.worker_poll_timeout,
        )
    except RedisTimeoutError:
        return None

    if result is None:
        return None
    _, raw = result
    return ReceiptJobPayload.model_validate_json(raw)


async def publish_ws_event(
    redis: Redis,
    *,
    upload_session_token: str,
    event: dict,
) -> None:
    message = WsEventMessage(
        upload_session_token=upload_session_token,
        event=event,
    )
    await redis.publish(settings.ws_events_channel, message.model_dump_json())


async def get_openrouter_credentials(db: AsyncSession) -> tuple[str, str] | None:
    secrets = SecretSettingsService(db)
    api_key = await secrets.get_secret("openrouter_api_key")
    if not api_key:
        return None

    config = SystemConfigRepository(db)
    model_item = await config.get_by_key("openrouter_vision_model")
    model = (
        model_item.value
        if model_item
        else CONFIG_DEFAULTS["openrouter_vision_model"]
    )
    return api_key, resolve_vision_model(model)


async def process_receipt_job(redis: Redis, job: ReceiptJobPayload) -> None:
    from app.services.receipt_processor import ReceiptProcessor

    await update_job_status(redis, job.job_id, "processing")
    async with AsyncSessionLocal() as db:
        try:
            processor = ReceiptProcessor(db, redis)
            await processor.process(job)
            await db.commit()
            await update_job_status(redis, job.job_id, "completed")
            logger.info("Completed receipt job %s", job.job_id)
        except Exception:
            logger.exception("Unhandled error for receipt job %s", job.job_id)
            await db.rollback()
            await update_job_status(redis, job.job_id, "failed")
            if job.upload_session_token:
                await publish_ws_event(
                    redis,
                    upload_session_token=job.upload_session_token,
                    event={
                        "type": "receipt_failed",
                        "data": {
                            "job_id": job.job_id,
                            "reason": "Gagal memproses resit.",
                        },
                    },
                )


async def receipt_worker_loop(stop_event: asyncio.Event) -> None:
    redis = create_worker_redis()
    await redis.ping()
    logger.info("In-process receipt worker started — queue: %s", settings.receipt_queue_key)

    try:
        while not stop_event.is_set():
            job = await dequeue_receipt_job(redis)
            if job is None:
                continue
            await process_receipt_job(redis, job)
    finally:
        await redis.aclose()
