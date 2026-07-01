import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from redis.asyncio import Redis
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import (
    CorporateAccountDep,
    CurrentUserDep,
    OrgAdminDep,
    OrgSuperadminDep,
    get_client_ip,
    get_db,
    get_redis_client,
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
from app.services.session import create_session

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
    current_user: CurrentUserDep,
    request: Request,
    response: Response,
    service: OrgService = Depends(_org_service),
    redis: Redis = Depends(get_redis_client),
) -> ApiResponse[OrgRegisterResponseData]:
    data = await service.register_org(current_user, payload)
    session_id = await create_session(
        redis,
        user_id=current_user.id,
        role="superadmin",
        org_id=data.org_id,
        active_context="corporate",
        email=current_user.email,
        ip=get_client_ip(request),
        user_agent=request.headers.get("User-Agent", ""),
    )
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_id,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
        max_age=settings.session_ttl_seconds,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.get("/me", response_model=ApiResponse[OrgMeResponseData])
async def get_my_org(
    current_session: CorporateAccountDep,
    current_user: CurrentUserDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgMeResponseData]:
    data = await service.get_my_org(current_user, org_id=current_session.org_id)
    return ApiResponse(success=True, data=data, message=None)


@router.patch("/policy", response_model=ApiResponse[OrgPolicyData])
async def update_org_policy(
    payload: OrgPolicyUpdateRequest,
    current_session: OrgSuperadminDep,
    current_user: CurrentUserDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgPolicyData]:
    data = await service.update_policy(current_user, payload, org_id=current_session.org_id)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/employees", response_model=ApiResponse[OrgEmployeeListResponse])
async def list_org_employees(
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    search: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgEmployeeListResponse]:
    data = await service.list_employees(
        current_user,
        org_id=current_session.org_id,
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
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgEmployeeItem]:
    data = await service.update_employee(
        current_user,
        user_id,
        payload,
        org_id=current_session.org_id,
    )
    return ApiResponse(success=True, data=data, message=None)


@router.delete(
    "/employees/{user_id}",
    response_model=ApiResponse[None],
    status_code=status.HTTP_200_OK,
)
async def remove_org_employee(
    user_id: uuid.UUID,
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[None]:
    await service.remove_employee_from_org(
        current_user,
        user_id,
        org_id=current_session.org_id,
    )
    return ApiResponse(success=True, data=None, message="Pekerja dikeluarkan.")


@router.get(
    "/pending-receipts",
    response_model=ApiResponse[OrgPendingReceiptListResponse],
)
async def list_org_pending_receipts(
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgPendingReceiptListResponse]:
    data = await service.list_pending_receipts(
        current_user,
        org_id=current_session.org_id,
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
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    receipt_service: ReceiptService = Depends(_receipt_service),
) -> ApiResponse[OrgBulkApproveResponse]:
    approved_count, skipped_count = await receipt_service.bulk_approve_org_pending(
        current_user,
        current_session,
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
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    tax_year: int | None = Query(default=None, ge=2000, le=2100),
    service: OrgAnalyticsService = Depends(_analytics_service),
) -> ApiResponse[OrgAnalyticsData]:
    if current_session.org_id is None:
        from app.core.exceptions import AppError

        raise AppError(message="Organisasi tidak dijumpai.", code="NOT_FOUND", status_code=404)
    year = tax_year or current_user.tax_year
    data = await service.get_analytics(current_session.org_id, tax_year=year)
    return ApiResponse(success=True, data=data, message=None)


@router.get("/export/csv")
async def export_org_payroll_csv(
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    tax_year: int = Query(ge=2000, le=2100),
    template: str = Query(default="generic"),
    service: ExportService = Depends(_export_service),
) -> Response:
    if current_session.org_id is None:
        from app.core.exceptions import AppError

        raise AppError(message="Organisasi tidak dijumpai.", code="NOT_FOUND", status_code=404)
    content, filename = await service.build_org_payroll_csv(
        current_session.org_id,
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
    current_session: OrgAdminDep,
    current_user: CurrentUserDep,
    service: OrgService = Depends(_org_service),
) -> ApiResponse[OrgEmployeeBulkImportResponse]:
    data = await service.bulk_import_employees(
        current_user,
        payload,
        org_id=current_session.org_id,
    )
    return ApiResponse(success=True, data=data, message=None)
