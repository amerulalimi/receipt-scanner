from __future__ import annotations

import hashlib
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import Receipt
from app.repositories.receipt import ReceiptRepository


async def compute_hash(file_bytes: bytes) -> str:
    """SHA-256 hex digest of raw file bytes."""
    return hashlib.sha256(file_bytes).hexdigest()


def derive_duplicate_image_hash(content_hash: str) -> str:
    """Unique storage hash for a duplicate row (satisfies global UNIQUE on image_hash)."""
    return hashlib.sha256(f"{content_hash}:{uuid.uuid4()}".encode()).hexdigest()


async def check_duplicate(
    db: AsyncSession,
    image_hash: str,
    user_id: uuid.UUID,
) -> Receipt | None:
    """Return existing non-duplicate receipt for this user and content hash, if any."""
    repo = ReceiptRepository(db)
    return await repo.get_by_content_hash_for_user(image_hash, user_id)
