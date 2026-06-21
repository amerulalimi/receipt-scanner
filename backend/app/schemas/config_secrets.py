from datetime import datetime

from pydantic import BaseModel, Field


class SecretSettingMaskedRead(BaseModel):
    key: str
    masked_value: str | None = None
    is_configured: bool
    updated_at: datetime | None = None


class SecretSettingUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=4096)


class SecretSettingsBulkUpdate(BaseModel):
    secrets: dict[str, str] = Field(min_length=1)
