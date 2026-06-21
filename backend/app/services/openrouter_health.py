from __future__ import annotations

import httpx
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.openrouter_key import validate_openrouter_key_format
from app.core.secret_keys import resolve_vision_model
from app.services.job_queue import get_openrouter_credentials

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
OPENROUTER_AUTH_URL = "https://openrouter.ai/api/v1/auth/key"


@dataclass(frozen=True)
class OpenRouterHealthResult:
    configured: bool
    key_format_valid: bool
    auth_ok: bool
    model_ok: bool
    model: str | None
    resolved_model: str | None
    message: str
    http_status: int | None = None


async def check_openrouter_health(db: AsyncSession) -> OpenRouterHealthResult:
    credentials = await get_openrouter_credentials(db)
    if credentials is None:
        return OpenRouterHealthResult(
            configured=False,
            key_format_valid=False,
            auth_ok=False,
            model_ok=False,
            model=None,
            resolved_model=None,
            message="OpenRouter API key belum dikonfigurasi di /admin/secrets.",
        )

    api_key, resolved_model = credentials
    config_model = resolved_model

    key_valid, key_message = validate_openrouter_key_format(api_key)
    if not key_valid:
        return OpenRouterHealthResult(
            configured=True,
            key_format_valid=False,
            auth_ok=False,
            model_ok=False,
            model=config_model,
            resolved_model=resolved_model,
            message=key_message,
        )

    headers = {"Authorization": f"Bearer {api_key.strip()}"}

    async with httpx.AsyncClient(timeout=20.0) as client:
        auth_response = await client.get(OPENROUTER_AUTH_URL, headers=headers)
        models_response = await client.get(OPENROUTER_MODELS_URL, headers=headers)

    auth_ok = auth_response.status_code == 200
    model_ok = False
    model_message = ""

    if models_response.status_code == 200:
        available_ids = {
            item.get("id")
            for item in models_response.json().get("data", [])
            if item.get("id")
        }
        model_ok = resolved_model in available_ids
        if not model_ok:
            model_message = (
                f"Model '{config_model}' tidak dijumpai di OpenRouter. "
                f"Cuba tukar ke google/gemini-2.5-flash di /admin/ai."
            )

    if auth_ok and model_ok:
        message = f"OpenRouter OK — model {resolved_model} tersedia."
    elif auth_ok and not model_ok:
        message = model_message
    elif auth_response.status_code == 401:
        message = "OpenRouter menolak API key (401). Semak key di openrouter.ai/keys."
    else:
        message = f"OpenRouter auth status {auth_response.status_code}."

    return OpenRouterHealthResult(
        configured=True,
        key_format_valid=True,
        auth_ok=auth_ok,
        model_ok=model_ok,
        model=config_model,
        resolved_model=resolved_model,
        message=message,
        http_status=auth_response.status_code,
    )
