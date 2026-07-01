from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.core.config import settings
from app.core.storage import get_receipt_file_path, get_user_upload_dir


@runtime_checkable
class StorageBackend(Protocol):
    async def upload_file(self, file_bytes: bytes, key: str, content_type: str) -> str: ...

    async def download_file(self, key: str) -> bytes: ...

    async def delete_file(self, key: str) -> None: ...

    async def get_presigned_url(self, key: str, expires_in: int = 900) -> str: ...


class LocalStorageBackend:
    def __init__(self) -> None:
        self._root = Path(settings.local_storage_path)

    async def upload_file(self, file_bytes: bytes, key: str, content_type: str) -> str:
        del content_type
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, file_bytes)
        return key

    async def download_file(self, key: str) -> bytes:
        path = get_receipt_file_path(key)
        if not path.is_file():
            path = self._root / key
        if not path.is_file():
            raise FileNotFoundError(key)
        return await asyncio.to_thread(path.read_bytes)

    async def delete_file(self, key: str) -> None:
        path = get_receipt_file_path(key)
        if path.is_file():
            await asyncio.to_thread(path.unlink)

    async def get_presigned_url(self, key: str, expires_in: int = 900) -> str:
        del key, expires_in
        return ""


def get_storage() -> StorageBackend:
    backend = settings.storage_backend.strip().lower()
    if backend in {"s3", "r2"}:
        from app.services.storage.s3 import S3StorageBackend

        return S3StorageBackend()
    return LocalStorageBackend()


def build_receipt_storage_key(user_id: uuid.UUID, file_type: str) -> str:
    return f"receipts/{user_id}/{uuid.uuid4()}.{file_type.lstrip('.')}"


def save_receipt_via_legacy_local(
    *,
    user_id: str,
    content: bytes,
    file_ext: str,
) -> str:
    """Bridge to existing local backend used for thumbnails."""
    from app.services.storage.local import get_local_storage_backend

    return get_local_storage_backend().save_receipt_file(
        user_id=user_id,
        content=content,
        file_ext=file_ext,
    )
