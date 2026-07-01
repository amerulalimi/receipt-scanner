from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import PlatformAdminDep, get_db
from app.schemas.common import ApiResponse
from app.schemas.config_settings import (
    SystemConfigBulkUpdate,
    SystemConfigRead,
    SystemConfigUpdate,
)
from app.services.system_config import SystemConfigService

router = APIRouter(prefix="/config/settings", tags=["config-settings"])


def _service(db: AsyncSession = Depends(get_db)) -> SystemConfigService:
    return SystemConfigService(db)


@router.get("", response_model=ApiResponse[list[SystemConfigRead]])
async def list_settings(
    _admin: PlatformAdminDep,
    service: SystemConfigService = Depends(_service),
) -> ApiResponse[list[SystemConfigRead]]:
    data = await service.list_all()
    return ApiResponse(success=True, data=data, message=None)


@router.put("/{key}", response_model=ApiResponse[SystemConfigRead])
async def upsert_setting(
    key: str,
    payload: SystemConfigUpdate,
    admin: PlatformAdminDep,
    service: SystemConfigService = Depends(_service),
) -> ApiResponse[SystemConfigRead]:
    data = await service.set(
        key,
        payload.value,
        updated_by=admin.id,
    )
    return ApiResponse(
        success=True,
        data=data,
        message="Tetapan berjaya dikemaskini.",
    )


@router.patch("", response_model=ApiResponse[list[SystemConfigRead]])
async def bulk_upsert_settings(
    payload: SystemConfigBulkUpdate,
    admin: PlatformAdminDep,
    service: SystemConfigService = Depends(_service),
) -> ApiResponse[list[SystemConfigRead]]:
    data = await service.bulk_set(
        payload.settings,
        updated_by=admin.id,
    )
    return ApiResponse(
        success=True,
        data=data,
        message="Tetapan berjaya dikemaskini.",
    )
