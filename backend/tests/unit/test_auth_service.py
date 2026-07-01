import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppError
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.auth import AuthService


def _make_user(**overrides) -> User:
    user = User(
        id=overrides.get("id", uuid.uuid4()),
        email=overrides.get("email", "test@example.com"),
        password_hash=overrides.get("password_hash", "hashed"),
        full_name=overrides.get("full_name", "Test User"),
        role=overrides.get("role", "individual"),
        account_type=overrides.get("account_type", "individual"),
        org_id=overrides.get("org_id"),
        tax_year=overrides.get("tax_year", 2025),
        tax_bracket=overrides.get("tax_bracket"),
        email_verified=overrides.get("email_verified", False),
        is_active=overrides.get("is_active", True),
    )
    return user


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock()
    return redis


@pytest.fixture
def auth_service(mock_db, mock_redis):
    return AuthService(mock_db, mock_redis)


@pytest.mark.unit
async def test_register_success(auth_service, mock_db, mock_redis):
    mock_repo = auth_service._users
    mock_repo.get_by_email = AsyncMock(return_value=None)
    created = _make_user()
    mock_repo.create = AsyncMock(return_value=created)
    mock_redis.pipeline = MagicMock(return_value=mock_redis)
    mock_redis.sadd = AsyncMock()
    mock_redis.setex = AsyncMock()
    mock_redis.execute = AsyncMock()
    mock_redis.smembers = AsyncMock(return_value=set())

    payload = RegisterRequest(
        email="new@example.com",
        password="password123",
        full_name="New User",
        account_type="individual",
    )

    with (
        patch(
            "app.services.auth.create_session",
            new_callable=AsyncMock,
            return_value="session-123",
        ),
        patch(
            "app.services.auth.AuditService.log",
            new_callable=AsyncMock,
        ),
    ):
        user, session_id = await auth_service.register(
            payload,
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    assert user.email == created.email
    assert session_id == "session-123"
    mock_repo.create.assert_awaited_once()


@pytest.mark.unit
async def test_register_duplicate_email(auth_service, mock_db):
    mock_repo = auth_service._users
    mock_repo.get_by_email = AsyncMock(return_value=_make_user())

    payload = RegisterRequest(
        email="exists@example.com",
        password="password123",
        full_name="User",
        account_type="individual",
    )

    with pytest.raises(AppError) as exc:
        await auth_service.register(
            payload,
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    assert exc.value.code == "EMAIL_EXISTS"
    assert exc.value.status_code == 400


@pytest.mark.unit
async def test_login_success(auth_service, mock_db, mock_redis):
    user = _make_user(password_hash="$2b$12$hashed")
    mock_repo = auth_service._users
    mock_repo.get_by_email = AsyncMock(return_value=user)

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=True,
        ),
        patch(
            "app.services.auth.create_session",
            new_callable=AsyncMock,
            return_value="sess-abc",
        ),
        patch.object(
            auth_service,
            "_login_rate_limit",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.auth.AuditService.log",
            new_callable=AsyncMock,
        ),
    ):
        result_user, session_id = await auth_service.login(
            email="test@example.com",
            password="password123",
            client_ip="127.0.0.1",
            user_agent="pytest",
        )

    assert result_user.id == user.id
    assert session_id == "sess-abc"


@pytest.mark.unit
async def test_login_wrong_password(auth_service, mock_db):
    user = _make_user()
    mock_repo = auth_service._users
    mock_repo.get_by_email = AsyncMock(return_value=user)

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=False,
        ),
        patch.object(
            auth_service,
            "_login_rate_limit",
            new_callable=AsyncMock,
        ),
    ):
        with pytest.raises(AppError) as exc:
            await auth_service.login(
                email="test@example.com",
                password="wrong",
                client_ip="127.0.0.1",
                user_agent="pytest",
            )

    assert exc.value.code == "INVALID_CREDENTIALS"
    assert exc.value.status_code == 401


@pytest.mark.unit
async def test_login_user_not_found(auth_service, mock_db):
    mock_repo = auth_service._users
    mock_repo.get_by_email = AsyncMock(return_value=None)

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=False,
        ),
        patch.object(
            auth_service,
            "_login_rate_limit",
            new_callable=AsyncMock,
        ),
    ):
        with pytest.raises(AppError) as exc:
            await auth_service.login(
                email="missing@example.com",
                password="password123",
                client_ip="127.0.0.1",
                user_agent="pytest",
            )

    assert exc.value.code == "INVALID_CREDENTIALS"


@pytest.mark.unit
async def test_login_inactive_user(auth_service, mock_db):
    user = _make_user(is_active=False)
    mock_repo = auth_service._users
    mock_repo.get_by_email = AsyncMock(return_value=user)

    with (
        patch(
            "app.services.auth.verify_password",
            return_value=True,
        ),
        patch.object(
            auth_service,
            "_login_rate_limit",
            new_callable=AsyncMock,
        ),
    ):
        with pytest.raises(AppError) as exc:
            await auth_service.login(
                email="test@example.com",
                password="password123",
                client_ip="127.0.0.1",
                user_agent="pytest",
            )

    assert exc.value.code == "ACCOUNT_DISABLED"
    assert exc.value.status_code == 403


@pytest.mark.unit
async def test_logout(auth_service, mock_redis):
    user_id = uuid.uuid4()
    with patch(
        "app.services.auth.delete_session",
        new_callable=AsyncMock,
    ) as mock_delete:
        await auth_service.logout(user_id=user_id, session_id="sess-1")
        mock_delete.assert_awaited_once_with(
            mock_redis,
            user_id=user_id,
            session_id="sess-1",
        )
