import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUserDep, OrgAdminDep, get_db
from app.schemas.common import ApiResponse
from app.schemas.household import (
    ClaimSuggestionData,
    HouseholdOverviewData,
    ReceiptReassignRequest,
    SpouseLinkRequest,
    SpouseLinkRespondRequest,
)
from app.services.household import HouseholdService

router = APIRouter(prefix="/household", tags=["household"])


def _household_service(db: AsyncSession = Depends(get_db)) -> HouseholdService:
    return HouseholdService(db)


@router.get("", response_model=ApiResponse[HouseholdOverviewData])
async def get_household_overview(
    current_user: CurrentUserDep,
    service: HouseholdService = Depends(_household_service),
) -> ApiResponse[HouseholdOverviewData]:
    data = await service.get_overview(current_user)
    return ApiResponse(success=True, data=data, message=None)


@router.post("/spouse-link", response_model=ApiResponse[dict], status_code=status.HTTP_201_CREATED)
async def request_spouse_link(
    payload: SpouseLinkRequest,
    current_user: CurrentUserDep,
    service: HouseholdService = Depends(_household_service),
) -> ApiResponse[dict]:
    link = await service.request_spouse_link(current_user, payload)
    return ApiResponse(
        success=True,
        data={"link_id": str(link.id), "status": link.status},
        message=None,
    )


@router.post("/spouse-link/{link_id}/respond", response_model=ApiResponse[dict])
async def respond_spouse_link(
    link_id: uuid.UUID,
    payload: SpouseLinkRespondRequest,
    current_user: CurrentUserDep,
    service: HouseholdService = Depends(_household_service),
) -> ApiResponse[dict]:
    link = await service.respond_to_link(current_user, link_id, payload)
    return ApiResponse(
        success=True,
        data={"link_id": str(link.id), "status": link.status},
        message=None,
    )


@router.delete("/spouse-link/{link_id}", response_model=ApiResponse[None])
async def dissolve_spouse_link(
    link_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: HouseholdService = Depends(_household_service),
) -> ApiResponse[None]:
    await service.dissolve_link(current_user, link_id)
    return ApiResponse(success=True, data=None, message="Pautan pasangan diputuskan.")


@router.post("/receipts/{receipt_id}/reassign", response_model=ApiResponse[None])
async def reassign_receipt_to_spouse(
    receipt_id: uuid.UUID,
    payload: ReceiptReassignRequest,
    current_user: CurrentUserDep,
    service: HouseholdService = Depends(_household_service),
) -> ApiResponse[None]:
    await service.reassign_receipt(
        current_user,
        receipt_id,
        target_user_id=payload.target_user_id,
    )
    return ApiResponse(success=True, data=None, message="Resit dipindahkan.")


@router.get(
    "/receipts/{receipt_id}/claim-suggestion",
    response_model=ApiResponse[ClaimSuggestionData],
)
async def get_claim_suggestion(
    receipt_id: uuid.UUID,
    current_user: CurrentUserDep,
    service: HouseholdService = Depends(_household_service),
) -> ApiResponse[ClaimSuggestionData]:
    data = await service.suggest_claim_owner(current_user, receipt_id)
    return ApiResponse(success=True, data=data, message=None)
