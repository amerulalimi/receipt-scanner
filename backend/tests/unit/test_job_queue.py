import uuid

import pytest

from app.services.job_queue import (
    enqueue_receipt_job,
    get_job_status,
    publish_ws_event,
)
from app.services.upload_session import QR_PREFIX, UploadSessionService


@pytest.mark.unit
async def test_enqueue_receipt_job(fake_redis, db_session, test_user):
    receipt_id = uuid.uuid4()
    job_id = await enqueue_receipt_job(
        fake_redis,
        receipt_id=receipt_id,
        user_id=test_user.id,
    )

    assert job_id
    queue_items = await fake_redis.lrange("receipt:jobs", 0, -1)
    assert len(queue_items) == 1

    status = await get_job_status(fake_redis, job_id)
    assert status is not None
    assert status["status"] == "queued"
    assert status["receipt_id"] == str(receipt_id)


@pytest.mark.unit
async def test_get_job_status_found(fake_redis):
    job_id = str(uuid.uuid4())
    await fake_redis.set(
        f"job:{job_id}",
        '{"status":"processing","receipt_id":"abc"}',
    )

    status = await get_job_status(fake_redis, job_id)
    assert status is not None
    assert status["status"] == "processing"


@pytest.mark.unit
async def test_get_job_status_not_found(fake_redis):
    assert await get_job_status(fake_redis, "missing-job") is None


@pytest.mark.unit
async def test_publish_ws_event(fake_redis):
    pubsub = fake_redis.pubsub()
    await pubsub.subscribe("ws:events")

    await publish_ws_event(
        fake_redis,
        upload_session_token="token-123",
        event={"type": "session_warned", "data": {"seconds_remaining": 120}},
    )

    message = None
    for _ in range(5):
        message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.2)
        if message is not None and message.get("type") == "message":
            break

    assert message is not None
    assert "token-123" in message["data"]
    await pubsub.aclose()
