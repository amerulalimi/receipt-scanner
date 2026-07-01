from contextlib import asynccontextmanager

import asyncio

import logging



from fastapi import FastAPI, HTTPException, Request, WebSocket

from fastapi.exceptions import RequestValidationError

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from sqlalchemy.exc import IntegrityError



from app.api.v1.router import api_router

from app.api.v1.routes.ws import dashboard_websocket

from app.core.config import settings

from app.core.database import engine

from app.core.exceptions import AppError

from app.core.logging import RequestIdMiddleware, setup_logging

from app.core.middleware import SecurityHeadersMiddleware

from app.core.rate_limit_middleware import AuthenticatedRateLimitMiddleware

from app.core.redis import close_redis, get_redis, init_redis

from app.core.startup import (

    check_worker_status,

    run_migrations,

    run_startup_checks,

    verify_database,

    verify_redis,

    verify_storage,

)

from app.core.storage import ensure_upload_root

from app.schemas.common import ApiErrorResponse, ApiResponse

from app.services.job_queue import receipt_worker_loop

from app.services.ws_subscriber import ws_events_subscriber_loop



logger = logging.getLogger(__name__)





@asynccontextmanager

async def lifespan(app: FastAPI):

    setup_logging()

    logger.info(

        "Starting Resit.my API v%s (%s)",

        app.version,

        settings.environment,

    )



    run_migrations()

    ensure_upload_root()

    redis = await init_redis()

    await run_startup_checks(engine, redis)



    stop_event = asyncio.Event()

    subscriber_task = asyncio.create_task(

        ws_events_subscriber_loop(get_redis(), stop_event),

    )

    worker_task: asyncio.Task | None = None

    if settings.run_in_process_worker:

        worker_task = asyncio.create_task(receipt_worker_loop(stop_event))

    yield

    stop_event.set()

    subscriber_task.cancel()

    if worker_task is not None:

        worker_task.cancel()

        try:

            await worker_task

        except asyncio.CancelledError:

            pass

    try:

        await subscriber_task

    except asyncio.CancelledError:

        pass

    await close_redis()

    await engine.dispose()





def create_app() -> FastAPI:

    app = FastAPI(

        title="Resit.my API",

        version="1.1.0",

        lifespan=lifespan,

    )



    app.add_middleware(AuthenticatedRateLimitMiddleware)

    app.add_middleware(SecurityHeadersMiddleware)

    app.add_middleware(RequestIdMiddleware)

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

        _exc: RequestValidationError,

    ) -> JSONResponse:

        body = ApiErrorResponse(

            success=False,

            message="Data tidak sah.",

            code="VALIDATION_ERROR",

        )

        return JSONResponse(status_code=422, content=body.model_dump())



    @app.exception_handler(HTTPException)

    async def http_exception_handler(

        _request: Request,

        exc: HTTPException,

    ) -> JSONResponse:

        detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)

        body = ApiErrorResponse(

            success=False,

            message=detail,

            code=str(exc.status_code),

        )

        return JSONResponse(status_code=exc.status_code, content=body.model_dump())



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

        _request: Request,

        exc: Exception,

    ) -> JSONResponse:

        logger.error("Unhandled exception: %s", exc, exc_info=True)

        body = ApiErrorResponse(

            success=False,

            message="Ralat dalaman. Sila cuba lagi.",

            code="INTERNAL_ERROR",

        )

        return JSONResponse(status_code=500, content=body.model_dump())



    @app.get("/health")

    async def health_check():

        db_status = "ok" if await verify_database(engine) else "error"

        redis_status = "ok"

        try:

            if not await verify_redis(get_redis()):

                redis_status = "error"

        except RuntimeError:

            redis_status = "error"



        storage_status = "ok" if await verify_storage() else "error"

        try:

            worker_status = await check_worker_status(get_redis())

        except RuntimeError:

            worker_status = "stopped"



        if db_status == "error" or redis_status == "error":

            overall = "down"

        elif storage_status == "error":

            overall = "degraded"

        else:

            overall = "ok"



        return ApiResponse(

            success=True,

            data={

                "status": overall,

                "version": app.version,

                "environment": settings.environment,

                "checks": {

                    "database": db_status,

                    "redis": redis_status,

                    "storage": storage_status,

                    "worker": worker_status,

                },

            },

            message=None,

        )



    @app.websocket("/ws/dashboard")

    async def ws_dashboard(websocket: WebSocket) -> None:

        await dashboard_websocket(websocket)



    app.include_router(api_router)



    return app





app = create_app()

