from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import CurrentUserDep, get_db
from app.schemas.claims import (
    ClaimCompareData,
    ClaimSummaryData,
    CompletenessScoreData,
    ReadyToFileData,
)
from app.schemas.common import ApiResponse
from app.services.borang_be import BorangBeService
from app.services.claims import ClaimsService
from app.services.engagement import EngagementService
from app.services.export import ExportService

router = APIRouter(prefix="/claims", tags=["claims"])


def _claims_service(db: AsyncSession = Depends(get_db)) -> ClaimsService:
    return ClaimsService(db)


def _borang_be_service(db: AsyncSession = Depends(get_db)) -> BorangBeService:
    return BorangBeService(db)


def _export_service(db: AsyncSession = Depends(get_db)) -> ExportService:
    return ExportService(db)


def _engagement_service(db: AsyncSession = Depends(get_db)) -> EngagementService:
    return EngagementService(db)


@router.get("/summary", response_model=ApiResponse[ClaimSummaryData])
async def get_claim_summary(
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    service: ClaimsService = Depends(_claims_service),
) -> ApiResponse[ClaimSummaryData]:
    data = await service.get_summary(current_user, tax_year=tax_year)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/compare", response_model=ApiResponse[ClaimCompareData])
async def get_claim_comparison(
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    service: ClaimsService = Depends(_claims_service),
) -> ApiResponse[ClaimCompareData]:
    data = await service.get_comparison(current_user, tax_year=tax_year)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/ready-to-file", response_model=ApiResponse[ReadyToFileData])
async def get_ready_to_file(
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    service: BorangBeService = Depends(_borang_be_service),
) -> ApiResponse[ReadyToFileData]:
    data = await service.get_ready_to_file(current_user, tax_year=tax_year)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/completeness", response_model=ApiResponse[CompletenessScoreData])
async def get_completeness_score(
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    service: EngagementService = Depends(_engagement_service),
) -> ApiResponse[CompletenessScoreData]:
    data = await service.get_completeness_score(current_user, tax_year=tax_year)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/export-zip")
async def export_receipts_zip(
    current_user: CurrentUserDep,
    tax_year: int = Query(ge=2000, le=2100),
    service: ExportService = Depends(_export_service),
) -> Response:
    content, filename = await service.build_receipts_zip(
        current_user,
        tax_year=tax_year,
    )
    return Response(
        content=content,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
