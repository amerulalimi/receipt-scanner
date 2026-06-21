import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUserDep, get_db
from app.schemas.common import ApiResponse
from app.schemas.notifications import (
    NotificationListResponse,
    NotificationPreferenceData,
    NotificationPreferenceUpdateRequest,
)
from app.services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


@router.get("/preferences", response_model=ApiResponse[NotificationPreferenceData])
async def get_notification_preferences(
    current_user: CurrentUserDep,
    service: NotificationService = Depends(_notification_service),
) -> ApiResponse[NotificationPreferenceData]:
    data = await service.get_preferences(current_user)
    return ApiResponse(success=True, data=data, message=None)


@router.patch("/preferences", response_model=ApiResponse[NotificationPreferenceData])
async def update_notification_preferences(
    payload: NotificationPreferenceUpdateRequest,
    current_user: CurrentUserDep,
    service: NotificationService = Depends(_notification_service),
) -> ApiResponse[NotificationPreferenceData]:
    data = await service.update_preferences(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.get("", response_model=ApiResponse[NotificationListResponse])
async def list_notifications(
    current_user: CurrentUserDep,
    service: NotificationService = Depends(_notification_service),
) -> ApiResponse[NotificationListResponse]:
    data = await service.sync_and_list(current_user)
    return ApiResponse(success=True, data=data, message=None)


@router.post("/{notification_id}/dismiss", response_model=ApiResponse[None])
async def dismiss_notification(
    notification_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: NotificationService = Depends(_notification_service),
) -> ApiResponse[None]:
    await service.dismiss(current_user, notification_id)
    return ApiResponse(success=True, data=None, message="Notifikasi ditutup.")
