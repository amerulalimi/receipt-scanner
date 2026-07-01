import hashlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services import dedup


@pytest.mark.unit
async def test_compute_hash_consistent():
    data = b"same-receipt-bytes"
    assert await dedup.compute_hash(data) == await dedup.compute_hash(data)
    assert await dedup.compute_hash(data) == hashlib.sha256(data).hexdigest()


@pytest.mark.unit
async def test_compute_hash_different():
    first = await dedup.compute_hash(b"file-a")
    second = await dedup.compute_hash(b"file-b")
    assert first != second


@pytest.mark.unit
async def test_check_duplicate_found():
    mock_db = AsyncMock()
    existing = MagicMock()
    with patch.object(
        dedup.ReceiptRepository,
        "get_by_content_hash_for_user",
        new_callable=AsyncMock,
        return_value=existing,
    ):
        result = await dedup.check_duplicate(mock_db, "abc123", MagicMock())
    assert result is existing


@pytest.mark.unit
async def test_check_duplicate_not_found():
    mock_db = AsyncMock()
    with patch.object(
        dedup.ReceiptRepository,
        "get_by_content_hash_for_user",
        new_callable=AsyncMock,
        return_value=None,
    ):
        result = await dedup.check_duplicate(mock_db, "abc123", MagicMock())
    assert result is None
