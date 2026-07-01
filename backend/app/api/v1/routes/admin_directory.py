import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PlatformAdminDep, get_db
from app.schemas.admin_directory import (
    AdminOrganizationDeleteData,
    AdminPaginatedOrganizationsData,
    AdminPaginatedUsersData,
    AdminUserDeleteData,
    RegistrationStatsData,
)
from app.schemas.common import ApiResponse
from app.services.admin_directory import AdminDirectoryService

router = APIRouter(prefix="/admin", tags=["admin-directory"])


def _service(db: AsyncSession = Depends(get_db)) -> AdminDirectoryService:
    return AdminDirectoryService(db)


@router.get("/users", response_model=ApiResponse[AdminPaginatedUsersData])
async def list_admin_users(
    _admin: PlatformAdminDep,
    service: AdminDirectoryService = Depends(_service),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
) -> ApiResponse[AdminPaginatedUsersData]:
    data = await service.list_users(page=page, limit=limit, search=search)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/users/stats", response_model=ApiResponse[RegistrationStatsData])
async def get_admin_user_stats(
    _admin: PlatformAdminDep,
    service: AdminDirectoryService = Depends(_service),
    granularity: str = Query(default="month", pattern="^(month|week|custom)$"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> ApiResponse[RegistrationStatsData]:
    data = await service.get_user_registration_stats(
        granularity=granularity,
        from_date=from_date,
        to_date=to_date,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.delete(
    "/users/{user_id}",
    response_model=ApiResponse[AdminUserDeleteData],
)
async def deactivate_admin_user(
    user_id: uuid.UUID,
    admin: PlatformAdminDep,
    service: AdminDirectoryService = Depends(_service),
) -> ApiResponse[AdminUserDeleteData]:
    data = await service.deactivate_user(user_id, admin_id=admin.id)
    return ApiResponse(
        success=True,
        data=data,
        message="Pengguna telah dinyahaktifkan.",
    )


@router.get("/organizations", response_model=ApiResponse[AdminPaginatedOrganizationsData])
async def list_admin_organizations(
    _admin: PlatformAdminDep,
    service: AdminDirectoryService = Depends(_service),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(default=None, max_length=200),
) -> ApiResponse[AdminPaginatedOrganizationsData]:
    data = await service.list_organizations(page=page, limit=limit, search=search)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/organizations/stats", response_model=ApiResponse[RegistrationStatsData])
async def get_admin_organization_stats(
    _admin: PlatformAdminDep,
    service: AdminDirectoryService = Depends(_service),
    granularity: str = Query(default="month", pattern="^(month|week|custom)$"),
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
) -> ApiResponse[RegistrationStatsData]:
    data = await service.get_organization_registration_stats(
        granularity=granularity,
        from_date=from_date,
        to_date=to_date,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.delete(
    "/organizations/{org_id}",
    response_model=ApiResponse[AdminOrganizationDeleteData],
)
async def suspend_admin_organization(
    org_id: uuid.UUID,
    admin: PlatformAdminDep,
    service: AdminDirectoryService = Depends(_service),
) -> ApiResponse[AdminOrganizationDeleteData]:
    data = await service.suspend_organization(org_id, admin_id=admin.id)
    return ApiResponse(
        success=True,
        data=data,
        message="Organisasi telah digantung.",
    )
