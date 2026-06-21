import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUserDep, OrgAdminDep, get_db, get_redis_client
from app.schemas.common import ApiResponse
from app.schemas.receipt import (
    ReceiptCreateRequest,
    ReceiptCreateResponse,
    ReceiptDetail,
    ReceiptDownloadData,
    ReceiptListResponse,
    ReceiptManualCreateRequest,
    ReceiptReviewRequest,
    ReceiptReviewResponse,
    ReceiptUpdateRequest,
    ReceiptUploadResponse,
)
from app.services.receipt import ReceiptService

router = APIRouter(prefix="/receipts", tags=["receipts"])


def _receipt_service(db: AsyncSession = Depends(get_db)) -> ReceiptService:
    return ReceiptService(db)


@router.get("", response_model=ApiResponse[ReceiptListResponse])
async def list_receipts(
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="created_at:desc"),
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptListResponse]:
    data = await service.list_receipts(
        current_user,
        tax_year=tax_year,
        category=category,
        status=status,
        page=page,
        limit=limit,
        sort=sort,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/upload",
    response_model=ApiResponse[ReceiptUploadResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_receipt(
    current_user: CurrentUserDep,
    files: list[UploadFile] = File(...),
    tax_year: int | None = Form(default=None, ge=2000, le=2100),
    service: ReceiptService = Depends(_receipt_service),
    redis: Redis = Depends(get_redis_client),
) -> ApiResponse[ReceiptUploadResponse]:
    uploads: list[tuple[str | None, str | None, bytes]] = []
    for upload in files:
        content = await upload.read()
        uploads.append((upload.filename, upload.content_type, content))

    data = await service.upload_receipts(
        current_user,
        uploads=uploads,
        redis=redis,
        tax_year=tax_year,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.get("/{receipt_id}", response_model=ApiResponse[ReceiptDetail])
async def get_receipt(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptDetail]:
    data = await service.get_receipt(current_user, receipt_id)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/{receipt_id}/file")
async def get_receipt_file(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> Response:
    content, media_type, file_name = await service.get_receipt_file(
        current_user,
        receipt_id,
    )
    headers = {}
    if file_name:
        headers["Content-Disposition"] = f'inline; filename="{file_name}"'
    return Response(content=content, media_type=media_type, headers=headers)


@router.get("/{receipt_id}/thumbnail")
async def get_receipt_thumbnail(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> Response:
    content, media_type = await service.get_receipt_thumbnail(
        current_user,
        receipt_id,
    )
    return Response(content=content, media_type=media_type)


@router.get(
    "/{receipt_id}/download",
    response_model=ApiResponse[ReceiptDownloadData],
)
async def get_receipt_download(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptDownloadData]:
    data = await service.get_receipt_download(current_user, receipt_id)
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "",
    response_model=ApiResponse[ReceiptCreateResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_receipt(
    payload: ReceiptCreateRequest,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptCreateResponse]:
    data = await service.create_receipt(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.patch("/{receipt_id}", response_model=ApiResponse[ReceiptDetail])
async def update_receipt(
    receipt_id: uuid.UUID,
    payload: ReceiptUpdateRequest,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptDetail]:
    data = await service.update_receipt(current_user, receipt_id, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/{receipt_id}/review",
    response_model=ApiResponse[ReceiptReviewResponse],
)
async def review_receipt(
    receipt_id: uuid.UUID,
    payload: ReceiptReviewRequest,
    current_user: OrgAdminDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptReviewResponse]:
    data = await service.review_receipt(current_user, receipt_id, payload)
    return ApiResponse(success=True, data=ReceiptReviewResponse(receipt=data), message=None)


@router.post(
    "/manual",
    response_model=ApiResponse[ReceiptDetail],
    status_code=status.HTTP_201_CREATED,
)
async def create_manual_receipt(
    payload: ReceiptManualCreateRequest,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[ReceiptDetail]:
    data = await service.create_manual_receipt(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.post("/{receipt_id}/reprocess", response_model=ApiResponse[ReceiptDetail])
async def reprocess_receipt(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
    redis: Redis = Depends(get_redis_client),
) -> ApiResponse[ReceiptDetail]:
    data = await service.reprocess_receipt(current_user, receipt_id, redis=redis)
    return ApiResponse(success=True, data=data, message=None)


@router.delete("/{receipt_id}", response_model=ApiResponse[None])
async def delete_receipt(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[None]:
    await service.delete_receipt(current_user, receipt_id)
    return ApiResponse(success=True, data=None, message="Resit dipadam")
