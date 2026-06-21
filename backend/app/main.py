from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.router import api_router
from app.api.v1.routes.ws import dashboard_websocket
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.redis import close_redis, get_redis, init_redis
from app.core.storage import ensure_upload_root
from app.schemas.common import ApiErrorResponse
from app.services.ws_subscriber import ws_events_subscriber_loop

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_upload_root()
    await init_redis()
    stop_event = asyncio.Event()
    subscriber_task = asyncio.create_task(
        ws_events_subscriber_loop(get_redis(), stop_event),
    )
    yield
    stop_event.set()
    subscriber_task.cancel()
    try:
        await subscriber_task
    except asyncio.CancelledError:
        pass
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Resit.my API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
        body = ApiErrorResponse(
            success=False,
            message=exc.message,
            code=exc.code,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=body.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = exc.errors()
        first = errors[0] if errors else {}
        field = ".".join(str(part) for part in first.get("loc", [])[1:])
        detail = first.get("msg", "Permintaan tidak sah")
        message = f"{field}: {detail}" if field else str(detail)
        body = ApiErrorResponse(
            success=False,
            message=message,
            code="VALIDATION_ERROR",
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        _request: Request,
        _exc: IntegrityError,
    ) -> JSONResponse:
        body = ApiErrorResponse(
            success=False,
            message="Gagal menyimpan tetapan. Akaun pengguna tidak sah.",
            code="VALIDATION_ERROR",
        )
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled error on %s", request.url.path)
        body = ApiErrorResponse(
            success=False,
            message="Ralat dalaman pelayan.",
            code="INTERNAL_ERROR",
        )
        return JSONResponse(status_code=500, content=body.model_dump())

    @app.get("/health")
    async def health_check():
        return {"data": {"status": "ok"}, "error": None}

    @app.websocket("/ws/dashboard")
    async def ws_dashboard(websocket: WebSocket) -> None:
        await dashboard_websocket(websocket)

    app.include_router(api_router)

    return app


app = create_app()
