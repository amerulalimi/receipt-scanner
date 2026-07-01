from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

WORKER_HEARTBEAT_KEY = "worker:heartbeat"


async def verify_database(engine: AsyncEngine) -> bool:
    try:
        async with asyncio.timeout(2):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database connectivity check failed")
        return False


async def verify_redis(redis: Redis | None = None) -> bool:
    client = redis
    owns_client = False
    if client is None:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        owns_client = True
    try:
        async with asyncio.timeout(2):
            await client.ping()
        return True
    except Exception:
        logger.exception("Redis connectivity check failed")
        return False
    finally:
        if owns_client and client is not None:
            await client.aclose()


def verify_openrouter_key() -> bool:
    if settings.openrouter_api_key.strip():
        return True
    logger.warning("OPENROUTER_API_KEY is not set — AI features will be degraded")
    return False


async def verify_storage() -> bool:
    backend = settings.storage_backend.strip().lower()
    try:
        async with asyncio.timeout(2):
            if backend == "local":
                path = Path(settings.local_storage_path)
                path.mkdir(parents=True, exist_ok=True)
                return path.exists()
            if backend in {"s3", "r2"}:
                required = [
                    settings.r2_account_id,
                    settings.r2_access_key_id,
                    settings.r2_secret_access_key,
                    settings.r2_bucket_name,
                ]
                return all(item.strip() for item in required)
        return False
    except Exception:
        logger.exception("Storage check failed")
        return False


async def check_worker_status(redis: Redis) -> str:
    try:
        async with asyncio.timeout(2):
            heartbeat = await redis.get(WORKER_HEARTBEAT_KEY)
            if heartbeat:
                return "running"
            if settings.run_in_process_worker:
                return "running"
            return "stopped"
    except Exception:
        return "stopped"


async def run_startup_checks(engine: AsyncEngine, redis: Redis) -> None:
    db_ok = await verify_database(engine)
    redis_ok = await verify_redis(redis)
    openrouter_ok = verify_openrouter_key()

    if settings.environment == "production":
        if not db_ok or not redis_ok:
            logger.critical(
                "Startup checks failed — database=%s redis=%s",
                db_ok,
                redis_ok,
            )
            raise SystemExit(1)
        if not openrouter_ok:
            logger.warning("Production started without OPENROUTER_API_KEY")
    else:
        if not db_ok:
            logger.warning("Database not reachable at startup")
        if not redis_ok:
            logger.warning("Redis not reachable at startup")


def run_migrations() -> None:
    if settings.environment == "test":
        return

    from alembic import command
    from alembic.config import Config

    try:
        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        logger.info("Database migrations applied successfully")
    except Exception:
        logger.critical("Database migration failed", exc_info=True)
        if settings.environment == "production":
            raise SystemExit(1) from None
        logger.warning("Continuing without migrations in %s", settings.environment)


async def touch_worker_heartbeat(redis: Redis) -> None:
    await redis.set(WORKER_HEARTBEAT_KEY, "1", ex=60)
