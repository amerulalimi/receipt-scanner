from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.core.config import settings
from app.core.deps import get_client_ip
from app.core.logging import user_id_ctx
from app.core.rate_limiter import enforce_rate_limit
from app.services.session import get_session

logger = logging.getLogger(__name__)

AUTHENTICATED_RATE_LIMIT = 300
AUTHENTICATED_RATE_WINDOW = 60

EXCLUDED_PATHS = frozenset(
    {
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    },
)

EXCLUDED_PREFIXES = (
    "/ws/",
)

SPECIAL_RATE_LIMIT_PATHS = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/register",
        "/api/v1/receipts/upload",
        "/api/v1/upload-sessions",
    },
)


def _is_upload_session_upload(path: str, method: str) -> bool:
    if method != "POST":
        return False
    parts = path.strip("/").split("/")
    return (
        len(parts) == 5
        and parts[0] == "api"
        and parts[1] == "v1"
        and parts[2] == "upload-sessions"
        and parts[4] == "upload"
    )


class AuthenticatedRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        path = request.url.path
        method = request.method

        if path in EXCLUDED_PATHS or path.startswith(EXCLUDED_PREFIXES):
            return await call_next(request)

        if path in SPECIAL_RATE_LIMIT_PATHS or _is_upload_session_upload(path, method):
            return await call_next(request)

        if not path.startswith("/api/v1/"):
            return await call_next(request)

        session_id = request.cookies.get(settings.session_cookie_name)
        if not session_id:
            return await call_next(request)

        from app.core.redis import get_redis

        try:
            redis = get_redis()
            session_data = await get_session(redis, session_id)
            if session_data is None:
                return await call_next(request)

            user_id = str(session_data["user_id"])
            user_id_ctx.set(user_id)

            if settings.auth_rate_limit_max <= 0:
                return await call_next(request)

            await enforce_rate_limit(
                redis,
                key_prefix="auth:global",
                identifier=user_id,
                max_requests=AUTHENTICATED_RATE_LIMIT,
                window_seconds=AUTHENTICATED_RATE_WINDOW,
            )
        except Exception as exc:
            from app.core.exceptions import AppError

            if isinstance(exc, AppError) and exc.code == "RATE_LIMITED":
                from fastapi.responses import JSONResponse

                from app.schemas.common import ApiErrorResponse

                body = ApiErrorResponse(
                    success=False,
                    message=exc.message,
                    code=exc.code,
                )
                return JSONResponse(status_code=429, content=body.model_dump())
            logger.exception("Rate limit middleware error")
        finally:
            user_id_ctx.set(None)

        return await call_next(request)
