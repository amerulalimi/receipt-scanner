import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import (
    CorporateAccountDep,
    OrgAdminDep,
    OrgSuperadminDep,
    get_db,
)
from app.schemas.common import ApiResponse
from app.schemas.org import (
    OrgBulkApproveResponse,
    OrgEmployeeBulkImportRequest,
    OrgEmployeeBulkImportResponse,
    OrgEmployeeListResponse,
    OrgEmployeeItem,
    OrgEmployeeUpdateRequest,
    OrgMeResponseData,
    OrgPendingReceiptListResponse,
    OrgPolicyData,
    OrgPolicyUpdateRequest,
    OrgRegisterRequest,
    OrgRegisterResponseData,
)
from app.schemas.org_analytics import OrgAnalyticsData
from app.services.org_analytics import OrgAnalyticsService
from app.services.export import ExportService
from app.services.org import OrgService
from app.services.receipt import ReceiptService

router = APIRouter(prefix="/org", tags=["org"])


def _org_service(db: AsyncSession = Depends(get_db)) -> OrgService:
    return OrgService(db)


def _receipt_service(db: AsyncSession = Depends(get_db)) -> ReceiptService:
    return ReceiptService(db)


def _export_service(db: AsyncSession = Depends(get_db)) -> ExportService:
    return ExportService(db)


def _analytics_service(db: AsyncSession = Depends(get_db)) -> OrgAnalyticsService:
    return OrgAnalyticsService(db)


@router.post(
    "/register",
    response_model=ApiResponse[OrgRegisterResponseData],
    status_code=status.HTTP_201_CREATED,
)
async def register_org(
    payload: OrgRegisterRequest,
    current_user: CorporateAccountDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgRegisterResponseData]:
    data = await service.register_org(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/me", response_model=ApiResponse[OrgMeResponseData])
async def get_my_org(
    current_user: CorporateAccountDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgMeResponseData]:
    data = await service.get_my_org(current_user)
    return ApiResponse(success=True, data=data, message=None)


@router.patch("/policy", response_model=ApiResponse[OrgPolicyData])
async def update_org_policy(
    payload: OrgPolicyUpdateRequest,
    current_user: OrgSuperadminDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgPolicyData]:
    data = await service.update_policy(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/employees", response_model=ApiResponse[OrgEmployeeListResponse])
async def list_org_employees(
    current_user: OrgAdminDep,
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgEmployeeListResponse]:
    data = await service.list_employees(
        current_user,
        search=search,
        status=status,
        page=page,
        limit=limit,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.patch(
    "/employees/{user_id}",
    response_model=ApiResponse[OrgEmployeeItem],
)
async def update_org_employee(
    user_id: uuid.UUID,
    payload: OrgEmployeeUpdateRequest,
    current_user: OrgAdminDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgEmployeeItem]:
    data = await service.update_employee(current_user, user_id, payload)
    return ApiResponse(success=True, data=data, message=None)


@router.delete(
    "/employees/{user_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
async def remove_org_employee(
    user_id: uuid.UUID,
    current_user: OrgAdminDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[None]:
    await service.remove_employee_from_org(current_user, user_id)
    return ApiResponse(success=True, data=None, message="Pekerja dikeluarkan.")


@router.get(
    "/pending-receipts",
    response_model=ApiResponse[OrgPendingReceiptListResponse],
)
async def list_org_pending_receipts(
    current_user: OrgAdminDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgPendingReceiptListResponse]:
    data = await service.list_pending_receipts(
        current_user,
        tax_year=tax_year,
        page=page,
        limit=limit,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.post(
    "/pending-receipts/bulk-approve",
    response_model=ApiResponse[OrgBulkApproveResponse],
)
async def bulk_approve_org_pending_receipts(
    current_user: OrgAdminDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    receipt_service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[OrgBulkApproveResponse]:
    approved_count, skipped_count = await receipt_service.bulk_approve_org_pending(
        current_user,
        tax_year=tax_year,
    )
    return ApiResponse(
        success=True,
        data=OrgBulkApproveResponse(
            approved_count=approved_count,
            skipped_count=skipped_count,
        ),
        message=None,
    )


@router.get("/analytics", response_model=ApiResponse[OrgAnalyticsData])
async def get_org_analytics(
    current_user: OrgAdminDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    service: OrgAnalyticsService = Depends(_analytics_service),
) -> ApiResponse[OrgAnalyticsData]:
    if current_user.org_id is None:
        from app.core.exceptions import AppError

        raise AppError(message="Organisasi tidak dijumpai.", code="NOT_FOUND", status_code=404)
    year = tax_year or current_user.tax_year
    data = await service.get_analytics(current_user.org_id, tax_year=year)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/export/csv")
async def export_org_payroll_csv(
    current_user: OrgAdminDep,
    tax_year: int = Query(ge=2000, le=2100),
    template: str = Query(default="generic"),
    service: ExportService = Depends(_export_service),
) -> Response:
    if current_user.org_id is None:
        from app.core.exceptions import AppError

        raise AppError(message="Organisasi tidak dijumpai.", code="NOT_FOUND", status_code=404)
    content, filename = await service.build_org_payroll_csv(
        current_user.org_id,
        tax_year=tax_year,
        template=template,
    )
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/employees/bulk-import",
    response_model=ApiResponse[OrgEmployeeBulkImportResponse],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_import_org_employees(
    payload: OrgEmployeeBulkImportRequest,
    current_user: OrgAdminDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgEmployeeBulkImportResponse]:
    data = await service.bulk_import_employees(current_user, payload)
    return ApiResponse(success=True, data=data, message=None)
