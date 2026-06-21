from pydantic import BaseModel


class OpenRouterHealthData(BaseModel):
    configured: bool
    key_format_valid: bool
    auth_ok: bool
    model_ok: bool
    model: str | None
    resolved_model: str | None
    message: str
    http_status: int | None = None
