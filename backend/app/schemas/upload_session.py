from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class UploadSessionCreateRequest(BaseModel):
    tax_year: int | None = Field(default=None, ge=2000, le=2100)


class UploadSessionCreateResponse(BaseModel):
    token: str
    upload_url: str
    qr_data: str
    inactivity_timeout: int
    expires_at: datetime


class UploadSessionValidateResponse(BaseModel):
    valid: bool
    user_name: str
    uploads_so_far: int
    inactivity_remaining: int


class UploadSessionUploadResponse(BaseModel):
    job_id: str
    session_inactivity_reset: bool = True
    new_inactivity_remaining: int


class UploadSessionKeepAliveResponse(BaseModel):
    inactivity_remaining: int


class UploadSessionCloseResponse(BaseModel):
    uploads_count: int
    message: str


class SessionClosedEventData(BaseModel):
    uploads_count: int
    total_amount: Decimal
