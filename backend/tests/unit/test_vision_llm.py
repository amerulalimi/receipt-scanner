import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.vision_llm import classify_receipt


@pytest.mark.unit
async def test_pdf_skipped():
    result = await classify_receipt(b"%PDF-1.4", "pdf")
    assert result["scan_status"] == "failed"
    assert "manual_review" in result["flags"]
    assert "PDF" in result["ai_nota"]


@pytest.mark.unit
async def test_successful_classification():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "content": json.dumps(
                        {
                            "merchant_name": "Klinik Test",
                            "receipt_date": "2025-06-14",
                            "total_amount": 320.0,
                            "ocr_confidence": 0.94,
                            "category": "perubatan",
                            "be_seksyen": "S.46(1)(b)",
                            "claimed_amount": 320.0,
                            "excluded_amount": 0,
                            "ai_confidence": 0.97,
                            "ai_nota": "Perubatan",
                            "is_mixed": False,
                            "line_items": [],
                        },
                    ),
                },
            },
        ],
    }

    with patch("app.services.vision_llm.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_response)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = instance

        result = await classify_receipt(
            b"fake-image",
            "jpg",
            api_key="test-key",
            model="test-model",
        )

    assert result["scan_status"] == "success"
    assert result["merchant_name"] == "Klinik Test"
    assert result["category"] == "perubatan"


@pytest.mark.unit
async def test_api_error_handling():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "server error"

    with patch("app.services.vision_llm.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_response)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = instance

        result = await classify_receipt(
            b"fake-image",
            "jpg",
            api_key="test-key",
            model="test-model",
        )

    assert result["scan_status"] == "failed"
    assert "manual_review" in result["flags"]


@pytest.mark.unit
async def test_invalid_json_response():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "not-json"}}],
    }

    with patch("app.services.vision_llm.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.post = AsyncMock(return_value=mock_response)
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = instance

        result = await classify_receipt(
            b"fake-image",
            "jpg",
            api_key="test-key",
            model="test-model",
        )

    assert result["scan_status"] == "failed"
    assert "manual_review" in result["flags"]
