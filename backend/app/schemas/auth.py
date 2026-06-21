import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    account_type: Literal["individual", "corporate"]


class RegisterResponseData(BaseModel):
    user_id: uuid.UUID
    email: str
    email_verified: bool


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class LoginResponseData(BaseModel):
    user_id: uuid.UUID
    role: str
    org_id: uuid.UUID | None
    full_name: str | None


class MeResponseData(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str | None
    role: str
    account_type: Literal["individual", "corporate"]
    org_id: uuid.UUID | None
    org_name: str | None = None
    tax_year: int
    tax_bracket: float | None = None
    email_verified: bool
    forwarding_address: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class VerifyEmailResponseData(BaseModel):
    email_verified: bool


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    tax_year: int = Field(ge=2000, le=2100)
    tax_bracket: float | None = Field(default=None, ge=0, le=100)


class SessionInfo(BaseModel):
    session_id: str
    ip: str
    user_agent: str
    created_at: str
    last_active: str
    is_current: bool
