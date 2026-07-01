import pytest

from tests.conftest import setup_org_via_api


@pytest.mark.integration
async def test_invite_employee_link_and_validate(org_client):
    await setup_org_via_api(org_client, email="invite@example.com")

    create = await org_client.post(
        "/api/v1/invites/employees",
        json={"type": "link"},
    )
    assert create.status_code == 201
    invite_url = create.json()["data"]["invite_url"]
    token = invite_url.rsplit("/", 1)[-1]

    validate = await org_client.get(f"/api/v1/invites/validate/{token}")
    assert validate.status_code == 200
    data = validate.json()["data"]
    assert data["valid"] is True
    assert data["role"] == "employee"


@pytest.mark.integration
async def test_invite_validate_not_found(org_client):
    response = await org_client.get("/api/v1/invites/validate/bad-token-xyz")
    assert response.status_code == 404
    assert response.json()["code"] == "INVITE_NOT_FOUND"


@pytest.mark.integration
async def test_invite_accept_creates_session(org_client):
    await setup_org_via_api(org_client, email="accept@example.com")

    create = await org_client.post(
        "/api/v1/invites/employees",
        json={"type": "email", "emails": ["newemp@example.com"]},
    )
    assert create.status_code == 201
    token = create.json()["data"]["invite_url"].rsplit("/", 1)[-1]

    accept = await org_client.post(
        "/api/v1/invites/accept",
        json={
            "token": token,
            "email": "newemp@example.com",
            "password": "password123",
            "full_name": "New Employee",
        },
    )
    assert accept.status_code == 201
    assert accept.json()["data"]["email"] == "newemp@example.com"
    assert "resit_sess" in accept.headers.get("set-cookie", "")


@pytest.mark.integration
async def test_invite_hr_admin_superadmin_only(org_client):
    await setup_org_via_api(org_client, email="sa@example.com")

    response = await org_client.post(
        "/api/v1/invites/hr-admin",
        json={"email": "hradmin@example.com"},
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["invite_url"] is not None
