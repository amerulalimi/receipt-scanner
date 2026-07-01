from __future__ import annotations

from functools import lru_cache
import logging

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = Field(
        ...,
        description="Async PostgreSQL URL (postgresql+asyncpg://...)",
    )
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)

    # ── Redis ───────────────────────────────────────────────────────────────
    redis_url: str = Field(..., description="Redis connection URL")

    # ── Session ─────────────────────────────────────────────────────────────
    session_secret: str = Field(
        default="changeme-min-32-chars-for-dev-only",
        min_length=32,
        description="Secret for signing session identifiers",
    )
    session_ttl_seconds: int = Field(default=28800, ge=60)
    session_cookie_name: str = Field(default="resit_sess")
    max_sessions_per_user: int = Field(default=3, ge=1)
    admin_session_cookie_name: str = Field(default="resit_admin_sess")
    admin_session_ttl_seconds: int = Field(default=28800, ge=60)
    max_admin_sessions_per_admin: int = Field(default=3, ge=1)

    # ── Storage ─────────────────────────────────────────────────────────────
    storage_backend: str = Field(
        default="local",
        description="Storage driver: local (dev) or r2/s3 (production)",
    )
    local_storage_path: str = Field(
        default="./storage/receipts",
        validation_alias=AliasChoices("LOCAL_STORAGE_PATH", "UPLOAD_DIR"),
        description="Local directory for receipt image storage (dev)",
    )
    r2_account_id: str = Field(default="")
    r2_access_key_id: str = Field(default="")
    r2_secret_access_key: str = Field(default="")
    r2_bucket_name: str = Field(default="")

    # ── AI ──────────────────────────────────────────────────────────────────
    openrouter_api_key: str = Field(default="")
    openrouter_vision_model: str = Field(default="google/gemini-2.5-flash")

    # ── App ─────────────────────────────────────────────────────────────────
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Public frontend base URL for CORS and upload links",
    )
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated allowed CORS origins",
    )

    # ── Email ───────────────────────────────────────────────────────────────
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    email_from: str = Field(default="noreply@resit.my")

    # ── Auth & rate limiting ─────────────────────────────────────────────────
    auth_rate_limit_max: int = Field(
        default=0,
        ge=0,
        description="Max auth attempts per window; 0 disables all rate limiting",
    )
    auth_rate_limit_window_seconds: int = Field(default=900, ge=60)
    email_verification_ttl_seconds: int = Field(default=86400, ge=300)
    invite_ttl_seconds: int = Field(default=172800, ge=3600)

    # ── Upload limits ────────────────────────────────────────────────────────
    max_upload_size_bytes: int = Field(default=10_485_760, ge=1)
    max_upload_files: int = Field(default=20, ge=1, le=50)
    upload_session_inactivity_seconds: int = Field(default=600, ge=60)
    upload_session_max_hours: int = Field(default=24, ge=1, le=48)
    upload_session_warn_seconds: int = Field(default=120, ge=30)
    run_in_process_worker: bool = Field(
        default=True,
        description="Run receipt queue worker inside FastAPI lifespan (dev). "
        "Set false when using a separate worker container.",
    )

    # ── Worker / realtime ───────────────────────────────────────────────────
    master_encryption_key: str = Field(
        default="",
        description="Fernet key for encrypting secrets in system_settings",
    )
    receipt_queue_key: str = Field(default="receipt:jobs")
    worker_poll_timeout: int = Field(default=5, ge=1)
    ws_events_channel: str = Field(default="ws:events")

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        if not value.startswith("postgresql+asyncpg://"):
            if value.startswith("sqlite+"):
                return value
            raise ValueError("DATABASE_URL must start with postgresql+asyncpg://")
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if not value.startswith("redis://") and not value.startswith("rediss://"):
            raise ValueError("REDIS_URL must start with redis://")
        return value

    @field_validator("storage_backend")
    @classmethod
    def validate_storage_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"local", "s3", "r2"}:
            raise ValueError("STORAGE_BACKEND must be 'local' or 's3'")
        return normalized

    @model_validator(mode="after")
    def validate_storage_credentials(self) -> Settings:
        backend = self.storage_backend.strip().lower()
        if backend in {"s3", "r2"}:
            missing = [
                name
                for name, val in (
                    ("R2_ACCOUNT_ID", self.r2_account_id),
                    ("R2_ACCESS_KEY_ID", self.r2_access_key_id),
                    ("R2_SECRET_ACCESS_KEY", self.r2_secret_access_key),
                    ("R2_BUCKET_NAME", self.r2_bucket_name),
                )
                if not val.strip()
            ]
            if missing and self.environment == "production":
                raise ValueError(
                    f"Missing required storage settings: {', '.join(missing)}",
                )
        if not self.openrouter_api_key.strip() and self.environment != "test":
            logger.warning("OPENROUTER_API_KEY is empty — AI features will degrade gracefully")
        return self

    @property
    def upload_dir(self) -> str:
        """Backward-compatible alias for local_storage_path."""
        return self.local_storage_path

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    @property
    def cookie_secure(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
