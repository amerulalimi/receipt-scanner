import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import (
    AdminSessionDataDep,
    PlatformAdminDep,
    get_client_ip,
    get_db,
    get_redis_client,
)
from app.core.exceptions import AppError
from app.schemas.admin_auth import AdminLoginRequest, AdminMeResponse, AdminResponse
from app.schemas.common import ApiResponse
from app.services.admin_auth import AdminAuthService

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


def _admin_auth_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> AdminAuthService:
    return AdminAuthService(db, redis)


def _set_admin_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=settings.admin_session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.admin_session_ttl_seconds,
    )


def _clear_admin_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.admin_session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post(
    "/login",
    response_model=ApiResponse[AdminResponse],
)
async def admin_login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    service: AdminAuthService = Depends(_admin_auth_service),
) -> ApiResponse[AdminResponse]:
    user_agent = request.headers.get("User-Agent", "")
    admin, session_id = await service.login(
        payload=payload,
        client_ip=get_client_ip(request),
        user_agent=user_agent,
    )
    _set_admin_session_cookie(response, session_id)
    return ApiResponse(
        success=True,
        data=service._admin_to_response(admin),
        message=None,
    )


@router.get("/me", response_model=ApiResponse[AdminMeResponse])
async def admin_get_me(
    current_admin: PlatformAdminDep,
    service: AdminAuthService = Depends(_admin_auth_service),
) -> ApiResponse[AdminMeResponse]:
    data = await service.get_me(current_admin)
    return ApiResponse(success=True, data=data, message=None)


@router.post("/logout", response_model=ApiResponse[None])
async def admin_logout(
    request: Request,
    response: Response,
    session_data: AdminSessionDataDep,
    service: AdminAuthService = Depends(_admin_auth_service),
) -> ApiResponse[None]:
    session_id = request.cookies.get(settings.admin_session_cookie_name)
    if session_id:
        await service.logout(
            admin_id=uuid.UUID(session_data["admin_id"]),
            session_id=session_id,
        )
    _clear_admin_session_cookie(response)
    return ApiResponse(success=True, data=None, message="Logged out")


@router.post("/refresh", response_model=ApiResponse[None])
async def admin_refresh_session(
    request: Request,
    response: Response,
    session_data: AdminSessionDataDep,
    service: AdminAuthService = Depends(_admin_auth_service),
) -> ApiResponse[None]:
    session_id = request.cookies.get(settings.admin_session_cookie_name)
    if not session_id:
        raise AppError(
            message="Sesi admin tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )
    await service.refresh_session(session_id=session_id, session_data=session_data)
    _set_admin_session_cookie(response, session_id)
    return ApiResponse(success=True, data=None, message=None)
