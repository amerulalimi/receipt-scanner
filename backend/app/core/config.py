from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(
        ...,
        description="Async PostgreSQL URL (postgresql+asyncpg://...)",
    )
    db_pool_size: int = Field(default=5, ge=1)
    db_max_overflow: int = Field(default=10, ge=0)

    redis_url: str = Field(..., description="Redis connection URL")

    debug: bool = Field(default=False)
    cors_origins: str = Field(
        default="http://localhost:3000",
        description="Comma-separated allowed CORS origins",
    )

    session_cookie_name: str = Field(default="resit_sess")
    session_ttl_seconds: int = Field(default=28800, ge=60)
    max_sessions_per_user: int = Field(default=3, ge=1)

    auth_rate_limit_max: int = Field(default=5, ge=1)
    auth_rate_limit_window_seconds: int = Field(default=900, ge=60)
    email_verification_ttl_seconds: int = Field(default=86400, ge=300)
    invite_ttl_seconds: int = Field(default=172800, ge=3600)
    upload_dir: str = Field(
        default="./storage/receipts",
        description="Local directory for receipt image storage (dev)",
    )
    storage_backend: str = Field(
        default="local",
        description="Storage driver: local (dev) or s3 (production)",
    )
    max_upload_size_bytes: int = Field(default=10_485_760, ge=1)
    max_upload_files: int = Field(default=20, ge=1, le=50)

    frontend_url: str = Field(
        default="http://localhost:3000",
        description="Public frontend base URL for QR upload links",
    )
    upload_session_inactivity_seconds: int = Field(default=600, ge=60)
    upload_session_max_hours: int = Field(default=24, ge=1, le=48)
    upload_session_warn_seconds: int = Field(default=120, ge=30)

    master_encryption_key: str = Field(
        ...,
        description="Fernet key for encrypting secrets in system_settings",
    )
    receipt_queue_key: str = Field(default="receipt:jobs")
    worker_poll_timeout: int = Field(default=5, ge=1)
    ws_events_channel: str = Field(default="ws:events")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def cookie_secure(self) -> bool:
        return not self.debug


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
