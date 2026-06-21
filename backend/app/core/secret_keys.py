ALLOWED_SECRET_KEYS = frozenset(
    {
        "openrouter_api_key",
    },
)

ALLOWED_CONFIG_KEYS = frozenset(
    {
        "openrouter_vision_model",
        "receipt_processing_enabled",
        "auth_rate_limit_max",
        "auth_rate_limit_window_seconds",
        "audit_retention_days",
        "receipt_retention_days",
    },
)

CONFIG_DEFAULTS: dict[str, str] = {
    "openrouter_vision_model": "google/gemini-2.5-flash",
    "receipt_processing_enabled": "true",
    "auth_rate_limit_max": "5",
    "auth_rate_limit_window_seconds": "900",
    "audit_retention_days": "365",
    "receipt_retention_days": "90",
}

# Legacy slugs that OpenRouter no longer serves.
DEPRECATED_VISION_MODELS: dict[str, str] = {
    "google/gemini-2.0-flash-001": "google/gemini-2.5-flash",
}


def resolve_vision_model(model: str) -> str:
    return DEPRECATED_VISION_MODELS.get(model, model)
