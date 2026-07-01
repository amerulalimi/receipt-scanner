from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AdminUserListItem(BaseModel):
    id: UUID
    full_name: str | None
    account_type: str
    email: str
    created_at: datetime
    is_active: bool


class AdminOrganizationListItem(BaseModel):
    id: UUID
    name: str
    email_domain: str
    status: str
    employee_count: int
    created_at: datetime


class AdminPaginatedUsersData(BaseModel):
    items: list[AdminUserListItem]
    page: int
    limit: int
    total: int
    total_pages: int


class AdminPaginatedOrganizationsData(BaseModel):
    items: list[AdminOrganizationListItem]
    page: int
    limit: int
    total: int
    total_pages: int


class RegistrationStatPoint(BaseModel):
    period: str
    label: str
    count: int
    cumulative: int


class RegistrationStatsData(BaseModel):
    series: list[RegistrationStatPoint]
    growth_percent: float
    growth_label: str
    total_in_range: int


class AdminUserDeleteData(BaseModel):
    id: UUID
    is_active: bool


class AdminOrganizationDeleteData(BaseModel):
    id: UUID
    status: str
