from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUserDep, PlatformAdminDep, get_db
from app.repositories.audit_log import AuditLogRepository
from app.schemas.common import ApiResponse
from app.schemas.system_admin import (
    AuditLogItem,
    AuditLogListResponse,
    ReliefCategoryItem,
    ReliefLimitCreateRequest,
    ReliefLimitItem,
    ReliefLimitUpdateRequest,
    RetentionPurgeResponse,
    SystemOverviewData,
)
from app.services.audit import AuditService
from app.services.retention import RetentionService
from app.services.system_admin import SystemAdminService

router = APIRouter(prefix="/config", tags=["config-admin"])


def _system_service(db: AsyncSession = Depends(get_db)) -> SystemAdminService:
    return SystemAdminService(db)


def _retention_service(db: AsyncSession = Depends(get_db)) -> RetentionService:
    return RetentionService(db)


@router.get("/relief-categories", response_model=ApiResponse[list[ReliefCategoryItem]])
async def list_relief_categories(
    service: SystemAdminService = Depends(_system_service),
) -> ApiResponse[list[ReliefCategoryItem]]:
    data = await service.list_relief_categories()
    return ApiResponse(success=True, data=data, message=None)


@router.get("/relief-limits", response_model=ApiResponse[list[ReliefLimitItem]])
async def list_relief_limits(
    _admin: PlatformAdminDep,
    service: SystemAdminService = Depends(_system_service),
) -> ApiResponse[list[ReliefLimitItem]]:
    data = await service.list_relief_limits()
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/relief-limits",
    response_model=ApiResponse[ReliefLimitItem],
    status_code=status.HTTP_201_CREATED,
)
async def create_relief_limit(
    payload: ReliefLimitCreateRequest,
    admin: PlatformAdminDep,
    service: SystemAdminService = Depends(_system_service),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ReliefLimitItem]:
    data = await service.create_relief_limit(payload, updated_by=admin.id)
    await AuditService(db).log(
        action="relief_limit.created",
        user_id=admin.id,
        resource="relief_limit",
        metadata={
            "category": payload.category,
            "limit_amount": str(payload.limit_amount),
        },
    )
    return ApiResponse(success=True, data=data, message="Had pelepasan ditambah.")


@router.patch(
    "/relief-limits/{category}",
    response_model=ApiResponse[ReliefLimitItem],
)
async def update_relief_limit(
    category: str,
    payload: ReliefLimitUpdateRequest,
    admin: PlatformAdminDep,
    service: SystemAdminService = Depends(_system_service),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ReliefLimitItem]:
    data = await service.update_relief_limit(
        category,
        payload,
        updated_by=admin.id,
    )
    await AuditService(db).log(
        action="relief_limit.updated",
        user_id=admin.id,
        resource="relief_limit",
        metadata={
            "category": category,
            "limit_amount": str(payload.limit_amount) if payload.limit_amount else None,
            "is_active": payload.is_active,
        },
    )
    return ApiResponse(success=True, data=data, message="Had pelepasan dikemas kini.")


@router.delete(
    "/relief-limits/{category}",
    response_model=ApiResponse[ReliefLimitItem],
)
async def deactivate_relief_limit(
    category: str,
    admin: PlatformAdminDep,
    service: SystemAdminService = Depends(_system_service),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[ReliefLimitItem]:
    data = await service.deactivate_relief_limit(category, updated_by=admin.id)
    await AuditService(db).log(
        action="relief_limit.deactivated",
        user_id=admin.id,
        resource="relief_limit",
        metadata={"category": category},
    )
    return ApiResponse(success=True, data=data, message="Had pelepasan dinyahaktifkan.")


@router.get("/audit-logs", response_model=ApiResponse[AuditLogListResponse])
async def list_audit_logs(
    _admin: PlatformAdminDep,
    action: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[AuditLogListResponse]:
    rows, total = await AuditLogRepository(db).list_recent(
        action=action,
        page=page,
        limit=limit,
    )
    items = [
        AuditLogItem(
            id=row.id,
            user_id=row.user_id,
            org_id=row.org_id,
            action=row.action,
            resource=row.resource,
            resource_id=row.resource_id,
            metadata=row.metadata_,
            ip_address=str(row.ip_address) if row.ip_address else None,
            created_at=row.created_at,
        )
        for row in rows
    ]
    return ApiResponse(
        success=True,
        data=AuditLogListResponse(items=items, total=total, page=page, limit=limit),
        message=None,
    )


@router.get("/system/overview", response_model=ApiResponse[SystemOverviewData])
async def get_system_overview(
    _admin: PlatformAdminDep,
    service: SystemAdminService = Depends(_system_service),
) -> ApiResponse[SystemOverviewData]:
    data = await service.get_overview()
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/system/purge-retention",
    response_model=ApiResponse[RetentionPurgeResponse],
    status_code=status.HTTP_200_OK,
)
async def purge_retention(
    admin: PlatformAdminDep,
    service: RetentionService = Depends(_retention_service),
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[RetentionPurgeResponse]:
    result = await service.purge()
    await AuditService(db).log(
        action="system.retention_purge",
        user_id=admin.id,
        resource="system",
        metadata=result,
    )
    return ApiResponse(
        success=True,
        data=RetentionPurgeResponse(**result),
        message="Pembersihan data lama selesai.",
    )
