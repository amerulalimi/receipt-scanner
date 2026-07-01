from fastapi import APIRouter, Depends, Request, Response, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import OrgAdminDep, OrgSuperadminDep, get_client_ip, get_db, get_redis_client
from app.schemas.common import ApiResponse
from app.schemas.org import (
    InviteAcceptRequest,
    InviteAcceptResponseData,
    InviteCreateResponseData,
    InviteEmployeesRequest,
    InviteHrAdminRequest,
    InviteValidateResponseData,
)
from app.services.org import OrgService

router = APIRouter(prefix="/invites", tags=["invites"])


def _org_service(db: AsyncSession = Depends(get_db)) -> OrgService:
    return OrgService(db)


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


@router.post(
    "/hr-admin",
    response_model=ApiResponse[InviteCreateResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def invite_hr_admin(
    payload: InviteHrAdminRequest,
    current_user: OrgSuperadminDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[InviteCreateResponseData]:
    data = await service.invite_hr_admin(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/employees",
    response_model=ApiResponse[InviteCreateResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def invite_employees(
    payload: InviteEmployeesRequest,
    current_user: OrgAdminDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[InviteCreateResponseData]:
    data = await service.invite_employees(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.get(
    "/validate/{token}",
    response_model=ApiResponse[InviteValidateResponseData],
)
async def validate_invite(
    token: str,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[InviteValidateResponseData]:
    data = await service.validate_invite(token)
    if not data.valid:
        from app.core.exceptions import AppError

        raise AppError(
            message="Jemputan tidak sah atau telah tamat tempoh.",
            code="INVITE_NOT_FOUND",
            status_code=404,
        )
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/accept",
    response_model=ApiResponse[InviteAcceptResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def accept_invite(
    payload: InviteAcceptRequest,
    request: Request,
    response: Response,
    service: OrgService = Depends(_org_service),
    redis: Redis = Depends(get_redis_client),
) -> ApiResponse[InviteAcceptResponseData]:
    user_agent = request.headers.get("User-Agent", "")
    data, session_id = await service.accept_invite(
        payload,
        client_ip=get_client_ip(request),
        user_agent=user_agent,
        redis=redis,
    )
    _set_session_cookie(response, session_id)
    return ApiResponse(success=True, data=data, message=None)
