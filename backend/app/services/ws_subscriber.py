from __future__ import annotations

import asyncio
import logging

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.receipt_job import WsEventMessage
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


async def ws_events_subscriber_loop(redis: Redis, stop_event: asyncio.Event) -> None:
    pubsub = redis.pubsub()
    await pubsub.subscribe(settings.ws_events_channel)
    logger.info("WS subscriber listening on %s", settings.ws_events_channel)

    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if message is None or message.get("type") != "message":
                continue

            try:
                payload = WsEventMessage.model_validate_json(message["data"])
                await ws_manager.emit(payload.upload_session_token, payload.event)
            except Exception:
                logger.exception("Failed to forward WS event")
    finally:
        await pubsub.unsubscribe(settings.ws_events_channel)
        await pubsub.aclose()
