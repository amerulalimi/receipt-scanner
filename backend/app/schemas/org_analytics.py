import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class OrgAnalyticsCategoryTrend(BaseModel):
    category: str
    month: date | None
    total_claimed: Decimal


class OrgAnalyticsEmployeeRank(BaseModel):
    user_id: uuid.UUID
    full_name: str | None
    email: str
    total_claimed: Decimal
    receipt_count: int


class OrgAnalyticsTurnaround(BaseModel):
    average_hours: float
    reviewed_count: int


class OrgAnalyticsRejectionReason(BaseModel):
    reason: str
    count: int


class OrgAnalyticsForecast(BaseModel):
    category: str
    approved_to_date: Decimal
    projected_year_end: Decimal
    org_limit: Decimal
    utilization_pct: float


class OrgAnalyticsData(BaseModel):
    tax_year: int
    category_trend: list[OrgAnalyticsCategoryTrend]
    top_employees: list[OrgAnalyticsEmployeeRank]
    turnaround: OrgAnalyticsTurnaround
    rejections: list[OrgAnalyticsRejectionReason]
    forecast: list[OrgAnalyticsForecast]
