import logging
from datetime import UTC, datetime
from decimal import Decimal
import uuid

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import hash_password, verify_password
from app.models.user import User

from app.repositories.user import UserRepository
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    RegisterRequest,
    SessionInfo,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.audit import AuditService
from app.core.rate_limiter import enforce_rate_limit, effective_rate_limit
from app.services.session import (
    create_session,
    delete_session,
    get_user_sessions,
    touch_session,
)

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._users = UserRepository(db)
        self._redis = redis

    def _available_contexts_for_user(self, user: User) -> list[str]:
        contexts = ["individual"]
        if user.org_id is not None and user.role in {"employee", "hr_admin", "superadmin"}:
            contexts.append("corporate")
        return contexts

    def _resolve_active_org_id(self, user: User, active_context: str) -> uuid.UUID | None:
        if active_context == "corporate":
            return user.org_id
        return None

    def _resolve_active_role(self, user: User, active_context: str) -> str:
        if active_context == "corporate":
            return user.role
        return "individual"

    def _user_to_response(self, user: User, *, active_context: str = "individual") -> UserResponse:
        tax_bracket = float(user.tax_bracket) if user.tax_bracket is not None else None
        active_org_id = self._resolve_active_org_id(user, active_context)
        return UserResponse(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            account_type=user.account_type,
            org_id=user.org_id,
            tax_year=user.tax_year,
            tax_bracket=tax_bracket,
            email_verified=user.email_verified,
            available_contexts=self._available_contexts_for_user(user),
            active_context=active_context,
            active_role=self._resolve_active_role(user, active_context),
            active_org_id=active_org_id,
        )

    async def _login_rate_limit(self, client_ip: str) -> None:
        await enforce_rate_limit(
            self._redis,
            key_prefix="auth:login",
            identifier=client_ip,
            max_requests=settings.auth_rate_limit_max,
            window_seconds=settings.auth_rate_limit_window_seconds,
        )

    async def _register_rate_limit(self, client_ip: str) -> None:
        await enforce_rate_limit(
            self._redis,
            key_prefix="auth:register",
            identifier=client_ip,
            max_requests=effective_rate_limit(10),
            window_seconds=3600,
        )

    async def register(
        self,
        payload: RegisterRequest,
        *,
        client_ip: str,
        user_agent: str,
    ) -> tuple[User, str]:
        email = payload.email.lower()
        await self._register_rate_limit(client_ip)
        existing = await self._users.get_by_email(email)
        if existing is not None:
            raise AppError(
                message="E-mel ini sudah didaftarkan.",
                code="EMAIL_EXISTS",
                status_code=400,
            )

        role = "individual"
        password_hash = hash_password(payload.password)
        full_name = payload.full_name.strip() if payload.full_name else None
        user = await self._users.create(
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            account_type=payload.account_type,
        )

        logger.info("TODO: send verification email to %s", email)

        session_id = await create_session(
            self._redis,
            user_id=user.id,
            role=user.role,
            org_id=user.org_id,
            active_context="individual",
            email=user.email,
            ip=client_ip,
            user_agent=user_agent,
        )

        await AuditService(self._db).log(
            action="auth.register",
            user_id=user.id,
            resource="user",
            resource_id=user.id,
            ip_address=client_ip,
        )

        return user, session_id

    async def login(
        self,
        *,
        payload: LoginRequest | None = None,
        email: str | None = None,
        password: str | None = None,
        client_ip: str,
        user_agent: str,
    ) -> tuple[User, str]:
        await self._login_rate_limit(client_ip)

        if payload is None:
            if email is None or password is None:
                raise ValueError("Either payload or email/password must be provided.")
            payload = LoginRequest(
                email=email,
                password=password,
                login_context="individual",
            )

        normalized_email = payload.email.lower()
        user = await self._users.get_by_email(normalized_email)

        if user is None or not verify_password(payload.password, user.password_hash):
            raise AppError(
                message="E-mel atau kata laluan tidak sah.",
                code="INVALID_CREDENTIALS",
                status_code=401,
            )

        if not user.is_active:
            raise AppError(
                message="Akaun ini telah dinyahaktifkan.",
                code="ACCOUNT_DISABLED",
                status_code=403,
            )

        available_contexts = self._available_contexts_for_user(user)
        if payload.login_context not in available_contexts:
            raise AppError(
                message="Konteks log masuk ini tidak tersedia untuk akaun anda.",
                code="FORBIDDEN_CONTEXT",
                status_code=403,
            )

        active_context = payload.login_context
        active_org_id = self._resolve_active_org_id(user, active_context)
        active_role = self._resolve_active_role(user, active_context)
        user.last_login_at = datetime.now(UTC)
        session_id = await create_session(
            self._redis,
            user_id=user.id,
            role=active_role,
            org_id=active_org_id,
            active_context=active_context,
            email=user.email,
            ip=client_ip,
            user_agent=user_agent,
        )

        await AuditService(self._db).log(
            action="auth.login",
            user_id=user.id,
            org_id=active_org_id,
            resource="session",
            metadata={"session_id": session_id, "active_context": active_context},
            ip_address=client_ip,
        )

        return user, session_id

    async def get_me(self, user: User, *, active_context: str) -> MeResponse:
        full_user = await self._users.get_by_id_with_org(user.id)
        if full_user is None:
            raise AppError(
                message="Akaun tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        org_name: str | None = None
        if active_context == "corporate" and full_user.organisation is not None:
            org_name = full_user.organisation.name

        base = self._user_to_response(full_user, active_context=active_context)
        return MeResponse(**base.model_dump(), org_name=org_name)

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

    async def verify_email(self, token: str) -> None:
        logger.info(
            "TODO: verify email token %s — Verification system coming in Phase 5",
            token[:8],
        )

    async def resend_verification_email(self, user: User) -> None:
        logger.info("TODO: send verification email to %s", user.email)

    async def update_profile(
        self,
        user: User,
        payload: UpdateProfileRequest,
        *,
        active_context: str,
    ) -> MeResponse:
        updates: dict = {}
        if payload.full_name is not None:
            updates["full_name"] = payload.full_name.strip()
        if payload.tax_year is not None:
            updates["tax_year"] = payload.tax_year
        if payload.tax_bracket is not None:
            updates["tax_bracket"] = Decimal(str(payload.tax_bracket))

        if not updates:
            return await self.get_me(user, active_context=active_context)

        updated = await self._users.update_profile(user.id, **updates)
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
            metadata=updates,
        )
        return await self.get_me(updated, active_context=active_context)

    async def list_sessions(
        self,
        *,
        user: User,
        current_session_id: str | None,
    ) -> list[SessionInfo]:
        sessions = await get_user_sessions(
            self._redis,
            user_id=user.id,
            current_session_id=current_session_id,
        )
        result: list[SessionInfo] = []
        for item in sessions:
            sid = str(item["session_id"])
            masked = f"{sid[:8]}..." if len(sid) > 8 else sid
            result.append(
                SessionInfo(
                    session_id=masked,
                    ip=str(item.get("ip") or "unknown"),
                    user_agent=str(item.get("user_agent") or "Unknown device"),
                    created_at=str(item["created_at"]),
                    last_active=str(item["last_active"]),
                    is_current=bool(item.get("is_current")),
                )
            )
        return result

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

        sessions = await get_user_sessions(
            self._redis,
            user_id=user.id,
            current_session_id=current_session_id,
        )
        full_session_ids = {str(item["session_id"]) for item in sessions}
        if session_id not in full_session_ids:
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
