from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import SuperadminDep, get_db
from app.schemas.common import ApiResponse
from app.schemas.config_secrets import (
    SecretSettingMaskedRead,
    SecretSettingUpdate,
    SecretSettingsBulkUpdate,
)
from app.schemas.openrouter_health import OpenRouterHealthData
from app.services.openrouter_health import check_openrouter_health
from app.services.secret_settings import SecretSettingsService

router = APIRouter(prefix="/config/secrets", tags=["config-secrets"])


def _service(db: AsyncSession = Depends(get_db)) -> SecretSettingsService:
    return SecretSettingsService(db)


@router.get("", response_model=ApiResponse[list[SecretSettingMaskedRead]])
async def list_secrets(
    _admin: SuperadminDep,
    service: SecretSettingsService = Depends(_service),
) -> ApiResponse[list[SecretSettingMaskedRead]]:
    data = await service.list_masked()
    return ApiResponse(success=True, data=data, message=None)


@router.get("/openrouter/health", response_model=ApiResponse[OpenRouterHealthData])
async def openrouter_health(
    _admin: SuperadminDep,
    db: AsyncSession = Depends(get_db),
) -> ApiResponse[OpenRouterHealthData]:
    result = await check_openrouter_health(db)
    data = OpenRouterHealthData(
        configured=result.configured,
        key_format_valid=result.key_format_valid,
        auth_ok=result.auth_ok,
        model_ok=result.model_ok,
        model=result.model,
        resolved_model=result.resolved_model,
        message=result.message,
        http_status=result.http_status,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.put("/{key}", response_model=ApiResponse[SecretSettingMaskedRead])
async def upsert_secret(
    key: str,
    payload: SecretSettingUpdate,
    admin: SuperadminDep,
    service: SecretSettingsService = Depends(_service),
) -> ApiResponse[SecretSettingMaskedRead]:
    data = await service.set_secret(
        key,
        payload.value,
        updated_by=admin.id,
    )
    return ApiResponse(
        success=True,
        data=data,
        message="Rahsia berjaya dikemaskini.",
    )


@router.patch("", response_model=ApiResponse[list[SecretSettingMaskedRead]])
async def bulk_upsert_secrets(
    payload: SecretSettingsBulkUpdate,
    admin: SuperadminDep,
    service: SecretSettingsService = Depends(_service),
) -> ApiResponse[list[SecretSettingMaskedRead]]:
    data = await service.bulk_set_secrets(
        payload.secrets,
        updated_by=admin.id,
    )
    return ApiResponse(
        success=True,
        data=data,
        message="Rahsia berjaya dikemaskini.",
    )
