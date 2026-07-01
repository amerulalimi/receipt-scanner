import logging
import uuid
from datetime import UTC, datetime

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.rate_limiter import enforce_rate_limit
from app.core.security import hash_password, verify_password
from app.models.platform_admin import PlatformAdmin
from app.repositories.platform_admin import PlatformAdminRepository
from app.schemas.admin_auth import AdminLoginRequest, AdminMeResponse, AdminResponse
from app.services.admin_session import (
    create_admin_session,
    delete_admin_session,
    touch_admin_session,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class AdminAuthService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._admins = PlatformAdminRepository(db)
        self._redis = redis

    def _admin_to_response(self, admin: PlatformAdmin) -> AdminResponse:
        return AdminResponse(
            admin_id=admin.id,
            email=admin.email,
            full_name=admin.full_name,
        )

    async def _login_rate_limit(self, client_ip: str) -> None:
        await enforce_rate_limit(
            self._redis,
            key_prefix="admin:login",
            identifier=client_ip,
            max_requests=settings.auth_rate_limit_max,
            window_seconds=settings.auth_rate_limit_window_seconds,
        )

    async def login(
        self,
        *,
        payload: AdminLoginRequest,
        client_ip: str,
        user_agent: str,
    ) -> tuple[PlatformAdmin, str]:
        await self._login_rate_limit(client_ip)

        normalized_email = payload.email.lower()
        admin = await self._admins.get_by_email(normalized_email)

        if admin is None or not verify_password(payload.password, admin.password_hash):
            raise AppError(
                message="E-mel atau kata laluan tidak sah.",
                code="INVALID_CREDENTIALS",
                status_code=401,
            )

        if not admin.is_active:
            raise AppError(
                message="Akaun admin ini telah dinyahaktifkan.",
                code="ACCOUNT_DISABLED",
                status_code=403,
            )

        admin.last_login_at = datetime.now(UTC)
        session_id = await create_admin_session(
            self._redis,
            admin_id=admin.id,
            email=admin.email,
            ip=client_ip,
            user_agent=user_agent,
        )

        await AuditService(self._db).log(
            action="admin.auth.login",
            user_id=admin.id,
            org_id=None,
            resource="admin_session",
            metadata={"session_id": session_id},
            ip_address=client_ip,
        )

        return admin, session_id

    async def get_me(self, admin: PlatformAdmin) -> AdminMeResponse:
        return AdminMeResponse(**self._admin_to_response(admin).model_dump())

    async def logout(self, *, admin_id: uuid.UUID, session_id: str) -> None:
        await delete_admin_session(
            self._redis,
            admin_id=admin_id,
            session_id=session_id,
        )

    async def refresh_session(
        self,
        *,
        session_id: str,
        session_data: dict,
    ) -> None:
        await touch_admin_session(self._redis, session_id, session_data)

    async def create_admin(
        self,
        *,
        email: str,
        password: str,
        full_name: str | None = None,
    ) -> PlatformAdmin:
        normalized_email = email.strip().lower()
        existing = await self._admins.get_by_email(normalized_email)
        if existing is not None:
            raise AppError(
                message="E-mel admin sudah wujud.",
                code="EMAIL_EXISTS",
                status_code=400,
            )

        return await self._admins.create(
            email=normalized_email,
            password_hash=hash_password(password),
            full_name=full_name,
        )
