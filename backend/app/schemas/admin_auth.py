import uuid

from pydantic import BaseModel, EmailStr, Field


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AdminResponse(BaseModel):
    admin_id: uuid.UUID
    email: str
    full_name: str | None = None


class AdminMeResponse(AdminResponse):
    pass
