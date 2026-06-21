import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


DigestFrequency = Literal["off", "monthly"]


class NotificationPreferenceData(BaseModel):
    email_enabled: bool
    in_app_enabled: bool
    digest_frequency: DigestFrequency


class NotificationPreferenceUpdateRequest(BaseModel):
    email_enabled: bool | None = None
    in_app_enabled: bool | None = None
    digest_frequency: DigestFrequency | None = None


class NotificationItem(BaseModel):
    id: uuid.UUID
    type: str
    severity: Literal["info", "warning"]
    title_my: str
    title_en: str
    message_my: str
    message_en: str
    action_href: str | None
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationItem]
    total: int


class MonthlyDigestLine(BaseModel):
    category: str
    label_my: str
    label_en: str
    claimed_this_month: float
    remaining_annual: float
    annual_limit: float
