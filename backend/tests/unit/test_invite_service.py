from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
import uuid

import pytest

from app.core.exceptions import AppError
from app.repositories.invite_token import InviteTokenRepository
from app.schemas.org import InviteAcceptRequest, InviteEmployeesRequest, InviteHrAdminRequest
from app.services.org import OrgService
from tests.conftest import seed_organisation


@pytest.mark.asyncio
async def test_create_hr_invite_expires_48h(db_session):
    org, admin = await seed_organisation(db_session)
    service = OrgService(db_session)

    with patch("app.services.org.send_invite_email", new_callable=AsyncMock):
        result = await service.invite_hr_admin(
            admin,
            InviteHrAdminRequest(email="hr@example.com"),
        )

    delta = result.expires_at.replace(tzinfo=UTC) - datetime.now(UTC)
    assert 47 * 3600 < delta.total_seconds() < 49 * 3600


@pytest.mark.asyncio
async def test_create_employee_link_invite(db_session):
    org, admin = await seed_organisation(db_session)
    service = OrgService(db_session)

    with patch("app.services.org.send_invite_email", new_callable=AsyncMock):
        result = await service.invite_employees(
            admin,
            InviteEmployeesRequest(type="link"),
        )

    assert result.type == "link"
    assert result.invite_url is not None
    delta = result.expires_at.replace(tzinfo=UTC) - datetime.now(UTC)
    assert delta.total_seconds() > 6 * 24 * 3600


@pytest.mark.asyncio
async def test_validate_invite_valid(db_session):
    org, admin = await seed_organisation(db_session)
    service = OrgService(db_session)

    with patch("app.services.org.send_invite_email", new_callable=AsyncMock):
        created = await service.invite_employees(
            admin,
            InviteEmployeesRequest(type="link"),
        )

    token = created.invite_url.rsplit("/", 1)[-1]
    data = await service.validate_invite(token)
    assert data.valid is True
    assert data.org_name == org.name
    assert data.role == "employee"


@pytest.mark.asyncio
async def test_validate_invite_expired(db_session):
    org, admin = await seed_organisation(db_session)
    repo = InviteTokenRepository(db_session)
    from app.models.invite_token import InviteToken

    invite = InviteToken(
        id=uuid.uuid4(),
        token="expired-token",
        org_id=org.id,
        invited_by=admin.id,
        role="employee",
        invite_type="email",
        invited_email="old@example.com",
        used=False,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
        created_at=datetime.now(UTC),
    )
    await repo.create(invite)
    await db_session.commit()

    service = OrgService(db_session)
    data = await service.validate_invite("expired-token")
    assert data.valid is False


@pytest.mark.asyncio
async def test_accept_invite_success(db_session, fake_redis):
    org, admin = await seed_organisation(db_session)
    service = OrgService(db_session)

    with patch("app.services.org.send_invite_email", new_callable=AsyncMock):
        created = await service.invite_employees(
            admin,
            InviteEmployeesRequest(type="link"),
        )

    token = created.invite_url.rsplit("/", 1)[-1]
    with patch("app.services.org.create_session", new_callable=AsyncMock, return_value="sess-1"):
        data, session_id = await service.accept_invite(
            InviteAcceptRequest(
                token=token,
                email="newhire@example.com",
                password="password123",
                full_name="New Hire",
            ),
            client_ip="127.0.0.1",
            user_agent="test",
            redis=fake_redis,
        )

    assert data.email == "newhire@example.com"
    assert session_id == "sess-1"


@pytest.mark.asyncio
async def test_accept_invite_domain_mismatch(db_session, fake_redis):
    org, admin = await seed_organisation(db_session)
    service = OrgService(db_session)

    with patch("app.services.org.send_invite_email", new_callable=AsyncMock):
        created = await service.invite_employees(
            admin,
            InviteEmployeesRequest(type="link"),
        )

    token = created.invite_url.rsplit("/", 1)[-1]
    with pytest.raises(AppError) as exc_info:
        await service.accept_invite(
            InviteAcceptRequest(
                token=token,
                email="wrong@other.example.com",
                password="password123",
                full_name="Wrong Domain",
            ),
            client_ip="127.0.0.1",
            user_agent="test",
            redis=fake_redis,
        )
    assert exc_info.value.code == "DOMAIN_MISMATCH"


@pytest.mark.asyncio
async def test_accept_invite_email_mismatch(db_session, fake_redis):
    org, admin = await seed_organisation(db_session)
    service = OrgService(db_session)

    with patch("app.services.org.send_invite_email", new_callable=AsyncMock):
        created = await service.invite_hr_admin(
            admin,
            InviteHrAdminRequest(email="hr@example.com"),
        )

    token = created.invite_url.rsplit("/", 1)[-1]
    with pytest.raises(AppError) as exc_info:
        await service.accept_invite(
            InviteAcceptRequest(
                token=token,
                email="other@example.com",
                password="password123",
                full_name="Mismatch",
            ),
            client_ip="127.0.0.1",
            user_agent="test",
            redis=fake_redis,
        )
    assert exc_info.value.code == "EMAIL_MISMATCH"
