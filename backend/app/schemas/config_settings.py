from datetime import datetime

from pydantic import BaseModel, Field


class SystemConfigRead(BaseModel):
    key: str
    value: str
    is_default: bool
    updated_at: datetime | None = None


class SystemConfigUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=1024)


class SystemConfigBulkUpdate(BaseModel):
    settings: dict[str, str] = Field(min_length=1)
