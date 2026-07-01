from dataclasses import dataclass
from collections.abc import AsyncGenerator, Callable
from typing import Annotated, Any
import uuid

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db as _get_db
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.models.platform_admin import PlatformAdmin
from app.models.user import User
from app.repositories.platform_admin import PlatformAdminRepository
from app.repositories.user import UserRepository
from app.services.admin_session import get_admin_session
from app.services.session import get_session


@dataclass
class AdminInSession:
    session_id: str
    admin_id: uuid.UUID
    email: str
    ip: str
    user_agent: str


@dataclass
class UserInSession:
    session_id: str
    user_id: uuid.UUID
    role: str
    org_id: uuid.UUID | None
    active_context: str
    email: str
    ip: str
    user_agent: str


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session


async def get_redis_client() -> AsyncGenerator[Redis, None]:
    yield get_redis()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def _session_to_user_in_session(session_id: str, data: dict[str, Any]) -> UserInSession:
    org_raw = data.get("org_id")
    return UserInSession(
        session_id=session_id,
        user_id=uuid.UUID(data["user_id"]),
        role=str(data["role"]),
        org_id=uuid.UUID(org_raw) if org_raw else None,
        active_context=str(data.get("active_context") or "individual"),
        email=str(data["email"]),
        ip=str(data.get("ip") or "unknown"),
        user_agent=str(data.get("user_agent") or "Unknown device"),
    )


async def get_session_data_dep(
    request: Request,
    redis: Redis = Depends(get_redis_client),
) -> dict[str, Any]:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise AppError(
            message="Sesi tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    session_data = await get_session(redis, session_id)
    if session_data is None:
        raise AppError(
            message="Sesi tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    return session_data


async def get_current_session(
    request: Request,
    redis: Redis = Depends(get_redis_client),
) -> UserInSession:
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        raise AppError(
            message="Sesi tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    session_data = await get_session(redis, session_id)
    if session_data is None:
        raise AppError(
            message="Sesi tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    return _session_to_user_in_session(session_id, session_data)


async def get_current_user(
    session_data: Annotated[dict[str, Any], Depends(get_session_data_dep)],
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = uuid.UUID(session_data["user_id"])
    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AppError(
            message="Akaun tidak dijumpai atau telah dinyahaktifkan.",
            code="UNAUTHORIZED",
            status_code=401,
        )
    return user


def require_role(allowed_roles: list[str]) -> Callable[..., Any]:
    allowed = frozenset(allowed_roles)

    async def _dependency(
        current_session: Annotated[UserInSession, Depends(get_current_session)],
    ) -> UserInSession:
        if current_session.role not in allowed:
            raise AppError(
                message="Akses ditolak.",
                code="FORBIDDEN",
                status_code=403,
            )
        return current_session

    return _dependency


async def get_admin_session_data_dep(
    request: Request,
    redis: Redis = Depends(get_redis_client),
) -> dict[str, Any]:
    session_id = request.cookies.get(settings.admin_session_cookie_name)
    if not session_id:
        raise AppError(
            message="Sesi admin tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    session_data = await get_admin_session(redis, session_id)
    if session_data is None:
        raise AppError(
            message="Sesi admin tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    return session_data


def _session_to_admin_in_session(session_id: str, data: dict[str, Any]) -> AdminInSession:
    return AdminInSession(
        session_id=session_id,
        admin_id=uuid.UUID(data["admin_id"]),
        email=str(data["email"]),
        ip=str(data.get("ip") or "unknown"),
        user_agent=str(data.get("user_agent") or "Unknown device"),
    )


async def get_current_admin_session(
    request: Request,
    redis: Redis = Depends(get_redis_client),
) -> AdminInSession:
    session_id = request.cookies.get(settings.admin_session_cookie_name)
    if not session_id:
        raise AppError(
            message="Sesi admin tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    session_data = await get_admin_session(redis, session_id)
    if session_data is None:
        raise AppError(
            message="Sesi admin tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    return _session_to_admin_in_session(session_id, session_data)


async def get_current_platform_admin(
    session_data: Annotated[dict[str, Any], Depends(get_admin_session_data_dep)],
    db: AsyncSession = Depends(get_db),
) -> PlatformAdmin:
    admin_id = uuid.UUID(session_data["admin_id"])
    admin = await PlatformAdminRepository(db).get_by_id(admin_id)
    if admin is None or not admin.is_active:
        raise AppError(
            message="Akaun admin tidak dijumpai atau telah dinyahaktifkan.",
            code="UNAUTHORIZED",
            status_code=401,
        )
    return admin


async def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
    current_session: Annotated[UserInSession, Depends(get_current_session)],
) -> User:
    if current_session.active_context == "corporate" or current_user.role != "superadmin":
        raise AppError(
            message="Akses ditolak. Hanya superadmin dibenarkan.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_user


ORG_MEMBER_ROLES = frozenset({"employee", "hr_admin", "superadmin"})
ORG_ADMIN_ROLES = frozenset({"hr_admin", "superadmin"})


async def require_corporate_account(
    current_session: Annotated[UserInSession, Depends(get_current_session)],
) -> UserInSession:
    if current_session.active_context != "corporate" or current_session.org_id is None:
        raise AppError(
            message="Akses organisasi hanya untuk akaun korporat.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_session


async def require_org_member(
    current_session: Annotated[UserInSession, Depends(get_current_session)],
) -> UserInSession:
    if current_session.active_context != "corporate" or current_session.org_id is None or current_session.role not in ORG_MEMBER_ROLES:
        raise AppError(
            message="Anda bukan ahli organisasi.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_session


async def require_org_admin(
    current_session: Annotated[UserInSession, Depends(get_current_session)],
) -> UserInSession:
    if current_session.active_context != "corporate" or current_session.org_id is None or current_session.role not in ORG_ADMIN_ROLES:
        raise AppError(
            message="Akses ditolak. Hanya HR admin dibenarkan.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_session


async def require_org_superadmin(
    current_session: Annotated[UserInSession, Depends(get_current_session)],
) -> UserInSession:
    if current_session.active_context != "corporate" or current_session.org_id is None or current_session.role != "superadmin":
        raise AppError(
            message="Akses ditolak. Hanya superadmin organisasi dibenarkan.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_session


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentSessionDep = Annotated[UserInSession, Depends(get_current_session)]
CurrentAdminSessionDep = Annotated[AdminInSession, Depends(get_current_admin_session)]
PlatformAdminDep = Annotated[PlatformAdmin, Depends(get_current_platform_admin)]
AdminSessionDataDep = Annotated[dict[str, Any], Depends(get_admin_session_data_dep)]
CorporateAccountDep = Annotated[User, Depends(require_corporate_account)]
SuperadminDep = Annotated[User, Depends(require_superadmin)]
OrgMemberDep = Annotated[User, Depends(require_org_member)]
OrgAdminDep = Annotated[User, Depends(require_org_admin)]
OrgSuperadminDep = Annotated[User, Depends(require_org_superadmin)]
SessionDataDep = Annotated[dict[str, Any], Depends(get_session_data_dep)]
