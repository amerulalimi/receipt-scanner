from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.core.storage import ReceiptStorageBackend
from app.services.storage.local import get_local_storage_backend
from app.services.storage.s3 import get_s3_storage_backend


@lru_cache
def get_receipt_storage() -> ReceiptStorageBackend:
    backend = settings.storage_backend.strip().lower()
    if backend == "s3":
        return get_s3_storage_backend()
    return get_local_storage_backend()
