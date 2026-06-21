import logging
import uuid

from redis.asyncio import Redis
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.secret_keys import CONFIG_DEFAULTS, resolve_vision_model
from app.repositories.system_config import SystemConfigRepository
from app.schemas.receipt_job import ReceiptJobPayload, WsEventMessage
from app.services.secret_settings import SecretSettingsService

logger = logging.getLogger(__name__)


def create_worker_redis() -> Redis:
    """Redis client for blocking BRPOP — socket timeout must exceed poll timeout."""
    poll_timeout = settings.worker_poll_timeout
    return Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=poll_timeout + 10,
    )


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
) -> None:
    payload = ReceiptJobPayload(
        receipt_id=receipt_id,
        user_id=user_id,
        upload_session_token=upload_session_token,
    )
    await redis.lpush(settings.receipt_queue_key, payload.model_dump_json())
    logger.info("Enqueued receipt job %s", receipt_id)


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
