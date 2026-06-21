from fastapi import APIRouter, Body, Depends, File, Request, UploadFile, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUserDep, SessionDataDep, get_db, get_redis_client
from app.schemas.common import ApiResponse
from app.schemas.upload_session import (
    UploadSessionCloseResponse,
    UploadSessionCreateRequest,
    UploadSessionCreateResponse,
    UploadSessionKeepAliveResponse,
    UploadSessionUploadResponse,
    UploadSessionValidateResponse,
)
from app.services.upload_session import UploadSessionService

router = APIRouter(prefix="/upload-sessions", tags=["upload-sessions"])


def _upload_session_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> UploadSessionService:
    return UploadSessionService(db, redis)


@router.post(
    "",
    response_model=ApiResponse[UploadSessionCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_upload_session(
    current_user: CurrentUserDep,
    session_data: SessionDataDep,
    payload: UploadSessionCreateRequest = Body(default_factory=UploadSessionCreateRequest),
    service: UploadSessionService = Depends(_upload_session_service),
) -> ApiResponse[UploadSessionCreateResponse]:
    data = await service.create_session(
        current_user,
        desktop_session_id=session_data["session_id"],
        tax_year=payload.tax_year,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.get(
    "/{token}/validate",
    response_model=ApiResponse[UploadSessionValidateResponse],
)
async def validate_upload_session(
    token: str,
    service: UploadSessionService = Depends(_upload_session_service),
) -> ApiResponse[UploadSessionValidateResponse]:
    data = await service.validate_token(token)
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/{token}/upload",
    response_model=ApiResponse[UploadSessionUploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_via_session(
    token: str,
    request: Request,
    file: UploadFile = File(...),
    service: UploadSessionService = Depends(_upload_session_service),
) -> ApiResponse[UploadSessionUploadResponse]:
    user_agent = request.headers.get("User-Agent", "")
    content = await file.read()
    data = await service.upload_receipt(
        token,
        filename=file.filename,
        content_type=file.content_type,
        content=content,
        user_agent=user_agent,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/{token}/keep-alive",
    response_model=ApiResponse[UploadSessionKeepAliveResponse],
)
async def keep_upload_session_alive(
    token: str,
    request: Request,
    service: UploadSessionService = Depends(_upload_session_service),
) -> ApiResponse[UploadSessionKeepAliveResponse]:
    user_agent = request.headers.get("User-Agent", "")
    data = await service.keep_alive(token, user_agent)
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/{token}/close",
    response_model=ApiResponse[UploadSessionCloseResponse],
)
async def close_upload_session(
    token: str,
    service: UploadSessionService = Depends(_upload_session_service),
) -> ApiResponse[UploadSessionCloseResponse]:
    data = await service.close_session(token)
    return ApiResponse(success=True, data=data, message=None)
