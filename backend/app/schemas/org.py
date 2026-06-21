import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field


class OrgRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    ssm_number: str = Field(min_length=5, max_length=20)
    email_domain: str = Field(min_length=3, max_length=100)


class OrgRegisterResponseData(BaseModel):
    org_id: uuid.UUID
    name: str
    email_domain: str
    domain_verified: bool


class OrgPolicyData(BaseModel):
    allowed_categories: list[str]
    require_hr_approval: bool
    max_receipts_per_month: int
    tax_year: int


class OrgMeResponseData(BaseModel):
    org_id: uuid.UUID
    name: str
    ssm_number: str
    email_domain: str
    domain_verified: bool
    total_employees: int
    policy: OrgPolicyData


class OrgPolicyUpdateRequest(BaseModel):
    allowed_categories: list[str] | None = None
    require_hr_approval: bool | None = None
    max_receipts_per_month: int | None = Field(default=None, ge=1, le=500)
    tax_year: int | None = Field(default=None, ge=2000, le=2100)


class OrgEmployeeItem(BaseModel):
    user_id: uuid.UUID
    full_name: str | None
    email: str
    role: str
    is_active: bool
    receipts_count: int
    total_claimed: float
    pending_count: int


class OrgEmployeeListResponse(BaseModel):
    items: list[OrgEmployeeItem]
    total: int
    page: int
    limit: int


class OrgPendingReceiptItem(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employee_name: str | None
    employee_email: str
    merchant_name: str | None
    receipt_date: date | None
    claimed_amount: float | None
    category: str | None
    be_seksyen: str | None
    status: str
    scan_status: str
    created_at: datetime


class OrgPendingReceiptListResponse(BaseModel):
    items: list[OrgPendingReceiptItem]
    total: int
    page: int
    limit: int


class OrgBulkApproveResponse(BaseModel):
    approved_count: int
    skipped_count: int


class OrgEmployeeUpdateRequest(BaseModel):
    is_active: bool


class InviteHrAdminRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)


class InviteEmployeesRequest(BaseModel):
    type: str = Field(pattern="^(email|link)$")
    emails: list[str] | None = None


class InviteCreateResponseData(BaseModel):
    invite_id: uuid.UUID | None = None
    email: str | None = None
    type: str
    invite_url: str | None = None
    expires_at: datetime
    invited_count: int = 1


class InviteValidateResponseData(BaseModel):
    valid: bool
    org_name: str | None = None
    role: str | None = None
    invited_email: str | None = None
    expires_at: datetime | None = None


class InviteAcceptRequest(BaseModel):
    token: str = Field(min_length=1, max_length=128)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)


class InviteAcceptResponseData(BaseModel):
    user_id: uuid.UUID
    email: str
    role: str
    org_id: uuid.UUID


class OrgEmployeeBulkImportRow(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    employee_code: str | None = Field(default=None, max_length=50)


class OrgEmployeeBulkImportRequest(BaseModel):
    employees: list[OrgEmployeeBulkImportRow] = Field(min_length=1, max_length=200)


class OrgEmployeeBulkImportResponse(BaseModel):
    invited_count: int
    invite_url: str | None = None
