from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.rule_engine import apply_rules


def _mock_limit(category: str, amount: str, seksyen: str | None = "S.46(1)(b)"):
    limit = MagicMock()
    limit.category = category
    limit.limit_amount = Decimal(amount)
    limit.be_seksyen = seksyen
    return limit


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.mark.unit
async def test_limit_not_exceeded(mock_db):
    with (
        patch(
            "app.services.rule_engine.get_active_relief_limits",
            new_callable=AsyncMock,
            return_value=[_mock_limit("perubatan", "8000")],
        ),
        patch(
            "app.services.rule_engine.ClaimLimitService.check_claim",
            new_callable=AsyncMock,
            return_value=MagicMock(
                would_exceed=False,
                relief_status=MagicMock(remaining=Decimal("7000")),
            ),
        ),
    ):
        result = await apply_rules(
            mock_db,
            MagicMock(),
            2025,
            {
                "category": "perubatan",
                "claimed_amount": 1000,
                "ocr_confidence": 0.9,
                "ai_confidence": 0.9,
            },
        )
    assert "limit_exceeded" not in result["flags"]
    assert result["claimed_amount"] == Decimal("1000")


@pytest.mark.unit
async def test_limit_exceeded(mock_db):
    with (
        patch(
            "app.services.rule_engine.get_active_relief_limits",
            new_callable=AsyncMock,
            return_value=[_mock_limit("perubatan", "8000")],
        ),
        patch(
            "app.services.rule_engine.ClaimLimitService.check_claim",
            new_callable=AsyncMock,
            return_value=MagicMock(
                would_exceed=True,
                relief_status=MagicMock(remaining=Decimal("500")),
            ),
        ),
    ):
        result = await apply_rules(
            mock_db,
            MagicMock(),
            2025,
            {
                "category": "perubatan",
                "claimed_amount": 9000,
                "ocr_confidence": 0.9,
                "ai_confidence": 0.9,
            },
        )
    assert "limit_exceeded" in result["flags"]
    assert result["claimed_amount"] == Decimal("500")


@pytest.mark.unit
async def test_low_ocr_confidence(mock_db):
    with (
        patch(
            "app.services.rule_engine.get_active_relief_limits",
            new_callable=AsyncMock,
            return_value=[_mock_limit("perubatan", "8000")],
        ),
        patch(
            "app.services.rule_engine.ClaimLimitService.check_claim",
            new_callable=AsyncMock,
            return_value=MagicMock(
                would_exceed=False,
                relief_status=MagicMock(remaining=Decimal("8000")),
            ),
        ),
    ):
        result = await apply_rules(
            mock_db,
            MagicMock(),
            2025,
            {
                "category": "perubatan",
                "claimed_amount": 100,
                "ocr_confidence": 0.5,
                "ai_confidence": 0.9,
            },
        )
    assert "low_ocr_confidence" in result["flags"]


@pytest.mark.unit
async def test_low_ai_confidence(mock_db):
    with (
        patch(
            "app.services.rule_engine.get_active_relief_limits",
            new_callable=AsyncMock,
            return_value=[_mock_limit("perubatan", "8000")],
        ),
        patch(
            "app.services.rule_engine.ClaimLimitService.check_claim",
            new_callable=AsyncMock,
            return_value=MagicMock(
                would_exceed=False,
                relief_status=MagicMock(remaining=Decimal("8000")),
            ),
        ),
    ):
        result = await apply_rules(
            mock_db,
            MagicMock(),
            2025,
            {
                "category": "perubatan",
                "claimed_amount": 100,
                "ocr_confidence": 0.9,
                "ai_confidence": 0.5,
            },
        )
    assert "low_ai_confidence" in result["flags"]


@pytest.mark.unit
async def test_mixed_items(mock_db):
    with (
        patch(
            "app.services.rule_engine.get_active_relief_limits",
            new_callable=AsyncMock,
            return_value=[_mock_limit("perubatan", "8000")],
        ),
        patch(
            "app.services.rule_engine.ClaimLimitService.check_claim",
            new_callable=AsyncMock,
            return_value=MagicMock(
                would_exceed=False,
                relief_status=MagicMock(remaining=Decimal("8000")),
            ),
        ),
    ):
        result = await apply_rules(
            mock_db,
            MagicMock(),
            2025,
            {
                "category": "perubatan",
                "claimed_amount": 100,
                "ocr_confidence": 0.9,
                "ai_confidence": 0.9,
                "is_mixed": True,
            },
        )
    assert "mixed_items" in result["flags"]


@pytest.mark.unit
async def test_unknown_category(mock_db):
    with patch(
        "app.services.rule_engine.get_active_relief_limits",
        new_callable=AsyncMock,
        return_value=[_mock_limit("perubatan", "8000")],
    ):
        result = await apply_rules(
            mock_db,
            MagicMock(),
            2025,
            {
                "category": "unknown_cat",
                "claimed_amount": 100,
                "ocr_confidence": 0.9,
                "ai_confidence": 0.9,
            },
        )
    assert result["category"] == "tidak_layak"
