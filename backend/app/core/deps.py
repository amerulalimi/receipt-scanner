from collections.abc import AsyncGenerator
from typing import Annotated, Any
import uuid

from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db as _get_db
from app.core.exceptions import AppError
from app.core.redis import get_redis
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.session import get_session_data, touch_session


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

    session_data = await get_session_data(redis, session_id)
    if session_data is None:
        raise AppError(
            message="Sesi tidak sah. Sila log masuk semula.",
            code="UNAUTHORIZED",
            status_code=401,
        )

    await touch_session(redis, session_id, session_data)
    return session_data


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


async def require_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "superadmin":
        raise AppError(
            message="Akses ditolak. Hanya superadmin dibenarkan.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_user


ORG_MEMBER_ROLES = frozenset({"employee", "hr_admin", "superadmin"})
ORG_ADMIN_ROLES = frozenset({"hr_admin", "superadmin"})


async def require_corporate_account(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.account_type != "corporate":
        raise AppError(
            message="Akses organisasi hanya untuk akaun korporat.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_user


async def require_org_member(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.org_id is None or current_user.role not in ORG_MEMBER_ROLES:
        raise AppError(
            message="Anda bukan ahli organisasi.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_user


async def require_org_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.org_id is None or current_user.role not in ORG_ADMIN_ROLES:
        raise AppError(
            message="Akses ditolak. Hanya HR admin dibenarkan.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_user


async def require_org_superadmin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.org_id is None or current_user.role != "superadmin":
        raise AppError(
            message="Akses ditolak. Hanya superadmin organisasi dibenarkan.",
            code="FORBIDDEN",
            status_code=403,
        )
    return current_user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CorporateAccountDep = Annotated[User, Depends(require_corporate_account)]
SuperadminDep = Annotated[User, Depends(require_superadmin)]
OrgMemberDep = Annotated[User, Depends(require_org_member)]
OrgAdminDep = Annotated[User, Depends(require_org_admin)]
OrgSuperadminDep = Annotated[User, Depends(require_org_superadmin)]
SessionDataDep = Annotated[dict[str, Any], Depends(get_session_data_dep)]
