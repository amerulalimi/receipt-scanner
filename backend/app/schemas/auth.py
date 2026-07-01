import uuid
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

AuthContext = Literal["individual", "corporate"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)
    account_type: Literal["individual", "corporate"] = "individual"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    login_context: AuthContext = "individual"


class UserResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str | None = None
    role: str
    account_type: Literal["individual", "corporate"]
    org_id: uuid.UUID | None = None
    tax_year: int
    tax_bracket: float | None = None
    email_verified: bool
    available_contexts: list[AuthContext] = Field(default_factory=list)
    active_context: AuthContext = "individual"
    active_role: str
    active_org_id: uuid.UUID | None = None


class MeResponse(UserResponse):
    org_name: str | None = None


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    tax_year: int | None = Field(default=None, ge=2000, le=2100)
    tax_bracket: float | None = Field(default=None, ge=0, le=100)


class SessionInfo(BaseModel):
    session_id: str
    ip: str
    user_agent: str
    created_at: str
    last_active: str
    is_current: bool


# Backward-compatible aliases
RegisterResponseData = UserResponse
LoginResponseData = UserResponse
MeResponseData = MeResponse
