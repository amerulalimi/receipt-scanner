from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.upload_session import UploadSession
from app.models.user import User
from app.repositories.upload_session import UploadSessionRepository
from app.repositories.user import UserRepository
from app.schemas.upload_session import (
    UploadSessionCloseResponse,
    UploadSessionCreateResponse,
    UploadSessionKeepAliveResponse,
    UploadSessionUploadResponse,
    UploadSessionValidateResponse,
)
from app.services.receipt import ReceiptService
from app.services.ws_manager import ws_manager


class UploadSessionService:
    ACTIVE_STATUSES = frozenset({"active", "warned"})

    def __init__(self, db: AsyncSession, redis: Redis) -> None:
        self._db = db
        self._redis = redis
        self._sessions = UploadSessionRepository(db)
        self._users = UserRepository(db)
        self._receipts = ReceiptService(db)

    async def create_session(
        self,
        user: User,
        desktop_session_id: str,
        *,
        tax_year: int | None = None,
    ) -> UploadSessionCreateResponse:
        await self._sessions.close_active_for_user(user.id)

        token = secrets.token_urlsafe(48)
        now = datetime.now(UTC)
        inactivity_secs = settings.upload_session_inactivity_seconds
        expires_at = now + timedelta(hours=settings.upload_session_max_hours)

        session = UploadSession(
            token=token,
            user_id=user.id,
            desktop_session=desktop_session_id,
            status="active",
            tax_year=tax_year or user.tax_year,
            inactivity_secs=inactivity_secs,
            expires_at=expires_at,
        )
        session = await self._sessions.create(session)
        await self._db.commit()

        upload_url = f"{settings.frontend_url}/upload/session/{token}"
        return UploadSessionCreateResponse(
            token=session.token,
            upload_url=upload_url,
            qr_data=upload_url,
            inactivity_timeout=inactivity_secs,
            expires_at=session.expires_at,
        )

    async def validate_token(self, token: str) -> UploadSessionValidateResponse:
        session = await self._require_valid_session(token)
        user = await self._require_user(session.user_id)
        remaining = self._inactivity_remaining(session)

        return UploadSessionValidateResponse(
            valid=True,
            user_name=user.full_name or user.email,
            uploads_so_far=session.uploads_count,
            inactivity_remaining=remaining,
        )

    async def upload_receipt(
        self,
        token: str,
        *,
        filename: str | None,
        content_type: str | None,
        content: bytes,
        user_agent: str,
    ) -> UploadSessionUploadResponse:
        session = await self._require_valid_session(token)
        self._bind_mobile_device(session, user_agent)

        user = await self._require_user(session.user_id)
        upload_result = await self._receipts.upload_receipt(
            user,
            filename=filename,
            content_type=content_type,
            content=content,
            upload_session_token=token,
            tax_year=session.tax_year,
            redis=self._redis,
        )

        now = datetime.now(UTC)
        session.last_upload_at = now
        session.uploads_count += 1
        if session.status == "warned":
            session.status = "active"
        await self._sessions.update(session)
        await self._db.commit()

        job_id = str(upload_result.job_ids[0])
        remaining = self._inactivity_remaining(session)

        return UploadSessionUploadResponse(
            job_id=job_id,
            session_inactivity_reset=True,
            new_inactivity_remaining=remaining,
        )

    async def keep_alive(self, token: str, user_agent: str) -> UploadSessionKeepAliveResponse:
        session = await self._require_valid_session(token)
        self._bind_mobile_device(session, user_agent)

        session.last_upload_at = datetime.now(UTC)
        if session.status == "warned":
            session.status = "active"
        await self._sessions.update(session)
        await self._db.commit()

        return UploadSessionKeepAliveResponse(
            inactivity_remaining=self._inactivity_remaining(session),
        )

    async def close_session(self, token: str) -> UploadSessionCloseResponse:
        session = await self._require_valid_session(token)

        now = datetime.now(UTC)
        session.status = "closed"
        session.closed_at = now
        await self._sessions.update(session)
        await self._db.commit()

        total_amount = await self._sessions.sum_receipts_since(
            session.user_id,
            session.created_at,
        )

        await ws_manager.emit(
            token,
            {
                "type": "session_closed",
                "data": {
                    "uploads_count": session.uploads_count,
                    "total_amount": total_amount,
                },
            },
        )

        return UploadSessionCloseResponse(
            uploads_count=session.uploads_count,
            message="Sesi selesai. Sambung di desktop anda.",
        )

    async def assert_user_owns_session(self, user: User, token: str) -> UploadSession:
        session = await self._sessions.get_by_token(token)
        if session is None:
            raise AppError(
                message="Sesi muat naik tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )
        if session.user_id != user.id:
            raise AppError(
                message="Akses ditolak untuk sesi ini.",
                code="FORBIDDEN",
                status_code=403,
            )
        return session

    async def _require_valid_session(self, token: str) -> UploadSession:
        session = await self._sessions.get_by_token(token)
        if session is None:
            raise AppError(
                message="Sesi muat naik tidak dijumpai.",
                code="NOT_FOUND",
                status_code=404,
            )

        now = datetime.now(UTC)
        if session.status not in self.ACTIVE_STATUSES:
            raise AppError(
                message="Sesi telah tamat. Sila imbas QR baru.",
                code="SESSION_EXPIRED",
                status_code=401,
            )

        if now >= session.expires_at:
            session.status = "expired"
            await self._sessions.update(session)
            await self._db.commit()
            await ws_manager.emit(
                token,
                {"type": "session_expired", "data": {"reason": "max_lifetime"}},
            )
            raise AppError(
                message="Sesi telah tamat. Sila imbas QR baru.",
                code="SESSION_EXPIRED",
                status_code=401,
            )

        if self._inactivity_remaining(session) <= 0:
            session.status = "expired"
            await self._sessions.update(session)
            await self._db.commit()
            await ws_manager.emit(
                token,
                {"type": "session_expired", "data": {"reason": "inactivity"}},
            )
            raise AppError(
                message="Sesi telah tamat. Sila imbas QR baru.",
                code="SESSION_EXPIRED",
                status_code=401,
            )

        remaining = self._inactivity_remaining(session)
        warn_threshold = settings.upload_session_warn_seconds
        if remaining <= warn_threshold and session.status == "active":
            session.status = "warned"
            await self._sessions.update(session)
            await self._db.commit()
            await ws_manager.emit(
                token,
                {
                    "type": "session_warned",
                    "data": {"seconds_remaining": remaining},
                },
            )

        return session

    async def _require_user(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            raise AppError(
                message="Akaun tidak dijumpai atau telah dinyahaktifkan.",
                code="NOT_FOUND",
                status_code=404,
            )
        return user

    def _inactivity_remaining(self, session: UploadSession) -> int:
        reference = session.last_upload_at or session.created_at
        elapsed = (datetime.now(UTC) - reference).total_seconds()
        return max(0, int(session.inactivity_secs - elapsed))

    def _bind_mobile_device(self, session: UploadSession, user_agent: str) -> None:
        normalized = user_agent[:500] if user_agent else "unknown"
        if session.mobile_ua is None:
            session.mobile_ua = normalized
            return
        if session.mobile_ua != normalized:
            raise AppError(
                message="Token sudah digunakan oleh peranti lain.",
                code="FORBIDDEN",
                status_code=403,
            )
