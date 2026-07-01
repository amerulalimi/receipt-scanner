import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import CurrentSessionDep, CurrentUserDep, SessionDataDep, get_client_ip, get_db, get_redis_client
from app.core.exceptions import AppError
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    SessionInfo,
    UpdateProfileRequest,
    UserResponse,
    VerifyEmailRequest,
)
from app.schemas.common import ApiResponse
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _auth_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> AuthService:
    return AuthService(db, redis)


def _set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.session_ttl_seconds,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.session_cookie_name,
        path="/",
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
    )


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[UserResponse]:
    user_agent = request.headers.get("User-Agent", "")
    user, session_id = await service.register(
        payload,
        client_ip=get_client_ip(request),
        user_agent=user_agent,
    )
    _set_session_cookie(response, session_id)
    return ApiResponse(
        success=True,
        data=service._user_to_response(user),
        message=None,
    )


@router.post(
    "/login",
    response_model=ApiResponse[UserResponse],
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[UserResponse]:
    user_agent = request.headers.get("User-Agent", "")
    user, session_id = await service.login(
        payload=payload,
        client_ip=get_client_ip(request),
        user_agent=user_agent,
    )
    _set_session_cookie(response, session_id)
    return ApiResponse(
        success=True,
        data=service._user_to_response(user, active_context=payload.login_context),
        message=None,
    )


@router.get("/me", response_model=ApiResponse[MeResponse])
async def get_me(
    current_user: CurrentUserDep,
    current_session: CurrentSessionDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[MeResponse]:
    data = await service.get_me(current_user, active_context=current_session.active_context)
    return ApiResponse(success=True, data=data, message=None)


@router.patch("/me", response_model=ApiResponse[MeResponse])
async def update_me(
    payload: UpdateProfileRequest,
    current_user: CurrentUserDep,
    current_session: CurrentSessionDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[MeResponse]:
    data = await service.update_profile(
        current_user,
        payload,
        active_context=current_session.active_context,
    )
    return ApiResponse(success=True, data=data, message="Tetapan akaun dikemas kini")


@router.post("/logout", response_model=ApiResponse[None])
async def logout(
    request: Request,
    response: Response,
    session_data: SessionDataDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[None]:
    session_id = request.cookies.get(settings.session_cookie_name)
    if session_id:
        await service.logout(
            user_id=uuid.UUID(session_data["user_id"]),
            session_id=session_id,
        )
    _clear_session_cookie(response)
    return ApiResponse(success=True, data=None, message="Logged out")


@router.post("/refresh", response_model=ApiResponse[None])
async def refresh_session(
    request: Request,
    response: Response,
    session_data: SessionDataDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[None]:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise AppError(
            message="Sesi tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )
    await service.refresh_session(session_id=session_id, session_data=session_data)
    _set_session_cookie(response, session_id)
    return ApiResponse(success=True, data=None, message=None)


@router.get("/sessions", response_model=ApiResponse[list[SessionInfo]])
async def list_sessions(
    request: Request,
    current_user: CurrentUserDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[list[SessionInfo]]:
    session_id = request.cookies.get(settings.session_cookie_name)
    data = await service.list_sessions(
        user=current_user,
        current_session_id=session_id,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.delete("/sessions/{session_id}", response_model=ApiResponse[None])
async def revoke_session(
    session_id: str,
    request: Request,
    current_user: CurrentUserDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[None]:
    current_session_id = request.cookies.get(settings.session_cookie_name)
    await service.revoke_session(
        user=current_user,
        session_id=session_id,
        current_session_id=current_session_id,
    )
    return ApiResponse(success=True, data=None, message="Sesi telah ditamatkan")


@router.post("/verify-email", response_model=ApiResponse[None])
async def verify_email(
    payload: VerifyEmailRequest,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[None]:
    await service.verify_email(payload.token)
    return ApiResponse(
        success=True,
        data=None,
        message="Verification system coming in Phase 5",
    )


@router.post("/resend-verification", response_model=ApiResponse[None])
async def resend_verification(
    current_user: CurrentUserDep,
    service: AuthService = Depends(_auth_service),
) -> ApiResponse[None]:
    await service.resend_verification_email(current_user)
    return ApiResponse(
        success=True,
        data=None,
        message="E-mel pengesahan akan dihantar (stub Phase 1)",
    )
