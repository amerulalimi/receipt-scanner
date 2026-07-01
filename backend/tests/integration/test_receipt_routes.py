import pytest

from tests.conftest import make_test_jpeg, register_and_login, wait_for_receipt_processed


@pytest.mark.integration
async def test_upload_single_file(receipt_client):
    await register_and_login(receipt_client)
    files = {"files": ("receipt.jpg", make_test_jpeg(), "image/jpeg")}
    response = await receipt_client.post("/api/v1/receipts/upload", files=files)
    assert response.status_code == 202
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["job_ids"]) == 1
    assert len(body["data"]["receipt_ids"]) == 1


@pytest.mark.integration
async def test_upload_pdf_flagged(receipt_client):
    await register_and_login(receipt_client, email="pdf@example.com")
    files = {"files": ("receipt.pdf", b"%PDF-1.4 test", "application/pdf")}
    response = await receipt_client.post("/api/v1/receipts/upload", files=files)
    assert response.status_code == 202
    receipt_id = response.json()["data"]["receipt_ids"][0]
    data = await wait_for_receipt_processed(receipt_client, receipt_id)
    assert data["scan_status"] == "success"


@pytest.mark.integration
async def test_upload_file_too_large(receipt_client):
    await register_and_login(receipt_client, email="large@example.com")
    huge = b"x" * (10 * 1024 * 1024 + 1)
    files = {"files": ("big.jpg", huge, "image/jpeg")}
    response = await receipt_client.post("/api/v1/receipts/upload", files=files)
    assert response.status_code == 422


@pytest.mark.integration
async def test_upload_duplicate(receipt_client):
    await register_and_login(receipt_client, email="dup@example.com")
    jpeg = make_test_jpeg()
    files = {"files": ("receipt.jpg", jpeg, "image/jpeg")}
    first = await receipt_client.post("/api/v1/receipts/upload", files=files)
    assert first.status_code == 202
    second = await receipt_client.post("/api/v1/receipts/upload", files=files)
    assert second.status_code == 202
    dup_id = second.json()["data"]["receipt_ids"][0]
    detail = await receipt_client.get(f"/api/v1/receipts/{dup_id}")
    assert detail.json()["data"]["status"] == "duplicate"


@pytest.mark.integration
async def test_get_receipts_empty(receipt_client):
    await register_and_login(receipt_client, email="empty@example.com")
    response = await receipt_client.get("/api/v1/receipts")
    assert response.status_code == 200
    assert response.json()["data"]["items"] == []


@pytest.mark.integration
async def test_get_receipts_with_data(receipt_client):
    await register_and_login(receipt_client, email="list@example.com")
    files = {"files": ("receipt.jpg", make_test_jpeg(), "image/jpeg")}
    await receipt_client.post("/api/v1/receipts/upload", files=files)
    response = await receipt_client.get("/api/v1/receipts")
    assert response.status_code == 200
    assert len(response.json()["data"]["items"]) == 1


@pytest.mark.integration
async def test_get_receipt_detail(receipt_client):
    await register_and_login(receipt_client, email="detail@example.com")
    upload = await receipt_client.post(
        "/api/v1/receipts/upload",
        files={"files": ("receipt.jpg", make_test_jpeg(), "image/jpeg")},
    )
    receipt_id = upload.json()["data"]["receipt_ids"][0]
    await wait_for_receipt_processed(receipt_client, receipt_id)
    response = await receipt_client.get(f"/api/v1/receipts/{receipt_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == receipt_id
    assert "flags" in data


@pytest.mark.integration
async def test_get_receipt_wrong_user(receipt_client):
    await register_and_login(receipt_client, email="owner@example.com")
    upload = await receipt_client.post(
        "/api/v1/receipts/upload",
        files={"files": ("receipt.jpg", make_test_jpeg(), "image/jpeg")},
    )
    receipt_id = upload.json()["data"]["receipt_ids"][0]

    await register_and_login(receipt_client, email="other@example.com")
    response = await receipt_client.get(f"/api/v1/receipts/{receipt_id}")
    assert response.status_code == 404


@pytest.mark.integration
async def test_patch_receipt(receipt_client):
    await register_and_login(receipt_client, email="patch@example.com")
    upload = await receipt_client.post(
        "/api/v1/receipts/upload",
        files={"files": ("receipt.jpg", make_test_jpeg(), "image/jpeg")},
    )
    receipt_id = upload.json()["data"]["receipt_ids"][0]
    await wait_for_receipt_processed(receipt_client, receipt_id)
    response = await receipt_client.patch(
        f"/api/v1/receipts/{receipt_id}",
        json={"notes": "Updated note"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["notes"] == "Updated note"


@pytest.mark.integration
async def test_delete_receipt(receipt_client):
    await register_and_login(receipt_client, email="delete@example.com")
    upload = await receipt_client.post(
        "/api/v1/receipts/upload",
        files={"files": ("receipt.jpg", make_test_jpeg(), "image/jpeg")},
    )
    receipt_id = upload.json()["data"]["receipt_ids"][0]
    delete_resp = await receipt_client.delete(f"/api/v1/receipts/{receipt_id}")
    assert delete_resp.status_code == 200
    listing = await receipt_client.get("/api/v1/receipts")
    assert listing.json()["data"]["items"] == []


@pytest.mark.integration
async def test_manual_entry(receipt_client):
    await register_and_login(receipt_client, email="manual@example.com")
    response = await receipt_client.post(
        "/api/v1/receipts/manual",
        json={
            "merchant_name": "Farmasi ABC",
            "receipt_date": "2025-06-14",
            "total_amount": 120.0,
            "category": "perubatan",
            "claimed_amount": 120.0,
            "notes": "Manual",
            "tax_year": 2025,
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["scan_status"] == "success"


@pytest.mark.integration
async def test_config_relief_categories(receipt_client):
    response = await receipt_client.get("/api/v1/config/relief-categories")
    assert response.status_code == 200
    categories = response.json()["data"]
    assert len(categories) == 7
