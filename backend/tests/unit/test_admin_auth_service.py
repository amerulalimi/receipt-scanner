from unittest.mock import AsyncMock, patch
import uuid

import pytest

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.platform_admin import PlatformAdmin
from app.schemas.admin_auth import AdminLoginRequest
from app.services.admin_auth import AdminAuthService


@pytest.mark.unit
async def test_admin_login_success(db_session, fake_redis):
    admin = PlatformAdmin(
        id=uuid.uuid4(),
        email="admin@admin.com",
        password_hash=hash_password("Senario@123"),
        full_name="Platform Admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    service = AdminAuthService(db_session, fake_redis)
    with patch("app.services.admin_auth.AuditService.log", new_callable=AsyncMock):
        result_admin, session_id = await service.login(
            payload=AdminLoginRequest(
                email="admin@admin.com",
                password="Senario@123",
            ),
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    assert result_admin.id == admin.id
    assert session_id


@pytest.mark.unit
async def test_admin_login_invalid_credentials(db_session, fake_redis):
    admin = PlatformAdmin(
        id=uuid.uuid4(),
        email="admin@admin.com",
        password_hash=hash_password("Senario@123"),
        full_name="Platform Admin",
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()

    service = AdminAuthService(db_session, fake_redis)
    with pytest.raises(AppError) as exc:
        await service.login(
            payload=AdminLoginRequest(
                email="admin@admin.com",
                password="wrong",
            ),
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    assert exc.value.code == "INVALID_CREDENTIALS"


@pytest.mark.unit
async def test_admin_login_inactive_account(db_session, fake_redis):
    admin = PlatformAdmin(
        id=uuid.uuid4(),
        email="admin@admin.com",
        password_hash=hash_password("Senario@123"),
        full_name="Platform Admin",
        is_active=False,
    )
    db_session.add(admin)
    await db_session.commit()

    service = AdminAuthService(db_session, fake_redis)
    with pytest.raises(AppError) as exc:
        await service.login(
            payload=AdminLoginRequest(
                email="admin@admin.com",
                password="Senario@123",
            ),
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    assert exc.value.code == "ACCOUNT_DISABLED"
