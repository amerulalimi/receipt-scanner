import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ReliefLimitItem(BaseModel):
    id: uuid.UUID
    category: str
    be_seksyen: str | None
    limit_amount: float
    description_my: str | None
    sort_order: int
    is_active: bool
    updated_at: datetime


class ReliefCategoryItem(BaseModel):
    category: str
    label: str
    be_seksyen: str | None


class ReliefLimitCreateRequest(BaseModel):
    category: str = Field(min_length=2, max_length=50, pattern=r"^[a-z][a-z0-9_]{1,48}$")
    limit_amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    be_seksyen: str | None = Field(default=None, max_length=20)
    description_my: str = Field(min_length=1, max_length=2000)
    sort_order: int = Field(default=0, ge=0, le=9999)


class ReliefLimitUpdateRequest(BaseModel):
    limit_amount: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    be_seksyen: str | None = Field(default=None, max_length=20)
    description_my: str | None = Field(default=None, max_length=2000)
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0, le=9999)

    @field_validator("limit_amount", "description_my", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: object) -> object:
        if value == "":
            return None
        return value


class AuditLogItem(BaseModel):
    id: int
    user_id: uuid.UUID | None
    org_id: uuid.UUID | None
    action: str
    resource: str | None
    resource_id: uuid.UUID | None
    metadata: dict | None
    ip_address: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    limit: int


class SystemOverviewData(BaseModel):
    auth_rate_limit_max: int
    auth_rate_limit_window_seconds: int
    audit_retention_days: int
    receipt_retention_days: int
    receipt_queue_depth: int
    total_audit_logs: int
    total_users: int = 0
    total_receipts: int = 0
    total_orgs: int = 0
    receipts_today: int = 0
    storage_backend: str = "local"
    worker_status: str = "stopped"
    redis_connected: bool = False
    db_connected: bool = True


class RetentionPurgeResponse(BaseModel):
    audit_logs_deleted: int
    receipts_deleted: int
    purged_receipts: int = 0
    purged_sessions: int = 0
    audit_retention_days: int
    receipt_retention_days: int
