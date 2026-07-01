from datetime import datetime

from pydantic import BaseModel


class OpenRouterModelOption(BaseModel):
    id: str
    name: str
    prompt_price_per_million_usd: float
    completion_price_per_million_usd: float
    image_token_price_per_million_usd: float


class OpenRouterModelsData(BaseModel):
    models: list[OpenRouterModelOption]
    fetched_at: datetime | None = None
    message: str | None = None
