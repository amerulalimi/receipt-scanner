from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from openrouter import OpenRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.openrouter_key import validate_openrouter_key_format
from app.schemas.openrouter_models import OpenRouterModelOption, OpenRouterModelsData
from app.services.job_queue import get_openrouter_credentials

MILLION = 1_000_000


def price_per_million(price_str: str | None) -> float:
    if not price_str:
        return 0.0
    try:
        return float(price_str) * MILLION
    except (TypeError, ValueError):
        return 0.0


def _map_model(model: object) -> OpenRouterModelOption | None:
    model_id = getattr(model, "id", None)
    if not model_id:
        return None

    pricing = getattr(model, "pricing", None)
    prompt = price_per_million(getattr(pricing, "prompt", None) if pricing else None)
    completion = price_per_million(
        getattr(pricing, "completion", None) if pricing else None
    )
    image_token = price_per_million(
        getattr(pricing, "image_token", None) if pricing else None
    )

    return OpenRouterModelOption(
        id=str(model_id),
        name=str(getattr(model, "name", None) or model_id),
        prompt_price_per_million_usd=prompt,
        completion_price_per_million_usd=completion,
        image_token_price_per_million_usd=image_token,
    )


@dataclass(frozen=True)
class OpenRouterModelsResult:
    data: OpenRouterModelsData
    http_status: int | None = None


async def list_openrouter_vision_models(db: AsyncSession) -> OpenRouterModelsResult:
    credentials = await get_openrouter_credentials(db)
    if credentials is None:
        return OpenRouterModelsResult(
            data=OpenRouterModelsData(
                models=[],
                fetched_at=None,
                message="OpenRouter API key belum dikonfigurasi di /admin/secrets.",
            ),
        )

    api_key, _resolved_model = credentials
    key_valid, key_message = validate_openrouter_key_format(api_key)
    if not key_valid:
        return OpenRouterModelsResult(
            data=OpenRouterModelsData(
                models=[],
                fetched_at=None,
                message=key_message,
            ),
        )

    try:
        async with OpenRouter(api_key=api_key.strip()) as client:
            response = await client.models.list_async(
                input_modalities="image",
                sort="pricing-low-to-high",
            )
    except Exception as exc:
        return OpenRouterModelsResult(
            data=OpenRouterModelsData(
                models=[],
                fetched_at=None,
                message=f"Gagal memuatkan senarai model OpenRouter: {exc}",
            ),
        )

    raw_models = getattr(response, "data", None) or []
    models: list[OpenRouterModelOption] = []
    for item in raw_models:
        mapped = _map_model(item)
        if mapped is not None:
            models.append(mapped)

    return OpenRouterModelsResult(
        data=OpenRouterModelsData(
            models=models,
            fetched_at=datetime.now(UTC),
            message=None if models else "Tiada model vision dijumpai di OpenRouter.",
        ),
    )
