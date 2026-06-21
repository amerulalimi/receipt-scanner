from datetime import UTC, datetime
from decimal import Decimal
import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.models.user import User
import secrets

from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginResponseData,
    MeResponseData,
    RegisterRequest,
    RegisterResponseData,
    SessionInfo,
    UpdateProfileRequest,
    VerifyEmailResponseData,
)
from app.services.audit import AuditService
from app.services.email import send_verification_email
from app.services.email_verification import (
    consume_verification_token,
    create_verification_token,
)
from app.services.rate_limit import check_rate_limit
from app.services.session import (
    create_session,
    delete_session,
    list_user_sessions,
    touch_session,
)
from app.services.system_config import SystemConfigService


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._redis = redis

    async def _auth_rate_limit(self, redis_key: str) -> None:
        config = SystemConfigService(self._db)
        await check_rate_limit(
            self._redis,
            key=redis_key,
            max_requests=await config.get_int(
                "auth_rate_limit_max",
                default=settings.auth_rate_limit_max,
            ),
            window_seconds=await config.get_int(
                "auth_rate_limit_window_seconds",
                default=settings.auth_rate_limit_window_seconds,
            ),
        )

    async def register(
        self,
        payload: RegisterRequest,
        *,
        client_ip: str,
    ) -> RegisterResponseData:
        await self._auth_rate_limit(f"rl:auth:register:{client_ip}")

        email = payload.email.lower()
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AppError(
                message="E-mel ini sudah didaftarkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        role = "individual"
        password_hash = hash_password(payload.password)
        user = await self._users.create(
            email=email,
            password_hash=password_hash,
            full_name=payload.full_name.strip(),
            role=role,
            account_type=payload.account_type,
        )

        token = await create_verification_token(self._redis, user.id)
        await send_verification_email(email=user.email, token=token)

        await AuditService(self._db).log(
            action="auth.register",
            user_id=user.id,
            resource="user",
            resource_id=user.id,
            ip_address=client_ip,
        )

        return RegisterResponseData(
            user_id=user.id,
            email=user.email,
            email_verified=user.email_verified,
        )

    async def login(
        self,
        *,
        email: str,
        password: str,
        client_ip: str,
        user_agent: str,
    ) -> tuple[LoginResponseData, str]:
        await self._auth_rate_limit(f"rl:auth:login:{client_ip}")

        normalized_email = email.lower()
        user = await self._users.get_by_email(normalized_email)

        if user is None or not verify_password(password, user.password_hash):
            raise AppError(
                message="E-mel atau kata laluan tidak sah.",
                code="UNAUTHORIZED",
                status_code=401,
            )

        if not user.is_active:
            raise AppError(
                message="Akaun ini telah dinyahaktifkan.",
                code="FORBIDDEN",
                status_code=403,
            )

        user.last_login_at = datetime.now(UTC)
        session_id = await create_session(
            self._redis,
            user_id=user.id,
            role=user.role,
            org_id=user.org_id,
            email=user.email,
            ip=client_ip,
            user_agent=user_agent,
        )

        data = LoginResponseData(
            user_id=user.id,
            role=user.role,
            org_id=user.org_id,
            full_name=user.full_name,
        )

        await AuditService(self._db).log(
            action="auth.login",
            user_id=user.id,
            org_id=user.org_id,
            resource="session",
            metadata={"session_id": session_id},
            ip_address=client_ip,
        )

        return data, session_id

    async def get_me(self, user: User) -> MeResponseData:
        full_user = await self._users.get_by_id_with_org(user.id)
        if full_user is None:
            raise AppError(
                message="Akaun tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        org_name: str | None = None
        if full_user.organisation is not None:
            org_name = full_user.organisation.name

        tax_bracket = (
            float(full_user.tax_bracket) if full_user.tax_bracket is not None else None
        )

        if full_user.forwarding_token is None:
            full_user.forwarding_token = secrets.token_hex(8)
            await self._db.flush()

        forwarding_address = (
            f"{full_user.forwarding_token}@receipts.resit.my"
            if full_user.forwarding_token
            else None
        )

        return MeResponseData(
            user_id=full_user.id,
            email=full_user.email,
            full_name=full_user.full_name,
            role=full_user.role,
            account_type=full_user.account_type,
            org_id=full_user.org_id,
            org_name=org_name,
            tax_year=full_user.tax_year,
            tax_bracket=tax_bracket,
            email_verified=full_user.email_verified,
            forwarding_address=forwarding_address,
        )

    async def logout(self, *, user_id: uuid.UUID, session_id: str) -> None:
        await delete_session(
            self._redis,
            user_id=user_id,
            session_id=session_id,
        )

    async def refresh_session(
        self,
        *,
        session_id: str,
        session_data: dict,
    ) -> None:
        await touch_session(self._redis, session_id, session_data)

    async def verify_email(self, token: str) -> VerifyEmailResponseData:
        user_id = await consume_verification_token(self._redis, token)
        if user_id is None:
            raise AppError(
                message="Token pengesahan tidak sah atau tamat tempoh.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppError(
                message="Akaun tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        if user.email_verified:
            return VerifyEmailResponseData(email_verified=True)

        await self._users.mark_email_verified(user.id)
        return VerifyEmailResponseData(email_verified=True)

    async def resend_verification_email(self, user: User) -> None:
        if user.email_verified:
            raise AppError(
                message="E-mel sudah disahkan.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        token = await create_verification_token(self._redis, user.id)
        await send_verification_email(email=user.email, token=token)

    async def update_profile(
        self,
        user: User,
        payload: UpdateProfileRequest,
    ) -> MeResponseData:
        tax_bracket = (
            Decimal(str(payload.tax_bracket))
            if payload.tax_bracket is not None
            else None
        )
        updated = await self._users.update_profile(
            user.id,
            full_name=payload.full_name.strip(),
            tax_year=payload.tax_year,
            tax_bracket=tax_bracket,
        )
        if updated is None:
            raise AppError(
                message="Akaun tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        await AuditService(self._db).log(
            action="user.profile_updated",
            user_id=user.id,
            org_id=user.org_id,
            resource="user",
            resource_id=user.id,
            metadata={
                "tax_year": payload.tax_year,
                "tax_bracket": payload.tax_bracket,
            },
        )
        return await self.get_me(updated)

    async def list_sessions(
        self,
        *,
        user: User,
        current_session_id: str | None,
    ) -> list[SessionInfo]:
        sessions = await list_user_sessions(
            self._redis,
            user_id=user.id,
            current_session_id=current_session_id,
        )
        return [
            SessionInfo(
                session_id=str(item["session_id"]),
                ip=str(item.get("ip") or "unknown"),
                user_agent=str(item.get("user_agent") or "Unknown device"),
                created_at=str(item["created_at"]),
                last_active=str(item["last_active"]),
                is_current=bool(item.get("is_current")),
            )
            for item in sessions
        ]

    async def revoke_session(
        self,
        *,
        user: User,
        session_id: str,
        current_session_id: str | None,
    ) -> None:
        if current_session_id and session_id == current_session_id:
            raise AppError(
                message="Gunakan log keluar untuk menamatkan sesi semasa.",
                code="VALIDATION_ERROR",
                status_code=422,
            )

        sessions = await list_user_sessions(
            self._redis,
            user_id=user.id,
            current_session_id=current_session_id,
        )
        if not any(item["session_id"] == session_id for item in sessions):
            raise AppError(
                message="Sesi tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        await delete_session(
            self._redis,
            user_id=user.id,
            session_id=session_id,
        )
