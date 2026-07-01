import pytest

from tests.conftest import register_and_login


@pytest.mark.integration
async def test_get_household_unlinked(phase6_client):
    await register_and_login(phase6_client, email="household-new@example.com")
    response = await phase6_client.get("/api/v1/household")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["partner"] is None
    assert data["accepted_link_id"] is None


@pytest.mark.integration
async def test_request_spouse_link(phase6_client):
    await register_and_login(phase6_client, email="link-requester@example.com")
    response = await phase6_client.post(
        "/api/v1/household/spouse-link",
        json={"partner_email": "partner-link@example.com"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "pending"


@pytest.mark.integration
async def test_respond_to_link(phase6_client):
    await register_and_login(phase6_client, email="respond-requester@example.com")
    create = await phase6_client.post(
        "/api/v1/household/spouse-link",
        json={"partner_email": "respond-partner@example.com"},
    )
    link_id = create.json()["data"]["link_id"]

    await register_and_login(phase6_client, email="respond-partner@example.com")
    response = await phase6_client.post(
        f"/api/v1/household/spouse-link/{link_id}/respond",
        json={"action": "accept"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "accepted"


@pytest.mark.integration
async def test_dissolve_link(phase6_client):
    await register_and_login(phase6_client, email="dissolve-req@example.com")
    create = await phase6_client.post(
        "/api/v1/household/spouse-link",
        json={"partner_email": "dissolve-par@example.com"},
    )
    link_id = create.json()["data"]["link_id"]

    await register_and_login(phase6_client, email="dissolve-par@example.com")
    await phase6_client.post(
        f"/api/v1/household/spouse-link/{link_id}/respond",
        json={"action": "accept"},
    )

    await register_and_login(phase6_client, email="dissolve-req@example.com")
    response = await phase6_client.delete(f"/api/v1/household/spouse-link/{link_id}")
    assert response.status_code == 200


@pytest.mark.integration
async def test_claim_suggestion(phase6_client):
    await register_and_login(phase6_client, email="claim-suggest@example.com")
    response = await phase6_client.get("/api/v1/household")
    assert response.status_code == 200

    from tests.conftest import TestSessionLocal, seed_approved_receipt
    from app.repositories.user import UserRepository

    async with TestSessionLocal() as session:
        user = await UserRepository(session).get_by_email("claim-suggest@example.com")
        assert user is not None
        receipt = await seed_approved_receipt(session, user_id=user.id)

    await register_and_login(phase6_client, email="claim-suggest@example.com")
    response = await phase6_client.get(
        f"/api/v1/household/receipts/{receipt.id}/claim-suggestion",
    )
    assert response.status_code == 200
    assert response.json()["data"]["suggestion"] == "self"
