from __future__ import annotations

from pathlib import Path

from app.core.config import settings

LEGACY_UPLOAD_DIR = Path("./uploads")
THUMB_SUFFIX = "_thumb.jpg"

IMAGE_EXTENSIONS = frozenset({"jpg", "jpeg", "png", "webp"})

MIME_BY_FILE_TYPE = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "pdf": "application/pdf",
}


def thumbnail_key_for(image_key: str) -> str:
    path = Path(image_key)
    return str(path.with_name(f"{path.stem}{THUMB_SUFFIX}"))


def get_upload_root() -> Path:
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def ensure_upload_root() -> Path:
    return get_upload_root()


def get_receipt_file_path(image_key: str) -> Path:
    primary = get_upload_root() / image_key
    if primary.is_file():
        return primary

    legacy = LEGACY_UPLOAD_DIR / image_key
    if legacy.is_file():
        return legacy

    return primary


def get_user_upload_dir(user_id: str) -> Path:
    user_dir = get_upload_root() / user_id
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


class ReceiptStorageBackend:
    def save_receipt_file(
        self,
        *,
        user_id: str,
        content: bytes,
        file_ext: str,
    ) -> str:
        raise NotImplementedError

    def read_receipt_file(self, image_key: str) -> bytes | None:
        raise NotImplementedError

    def read_thumbnail(self, image_key: str) -> bytes | None:
        raise NotImplementedError

    def receipt_file_exists(self, image_key: str) -> bool:
        raise NotImplementedError


def build_receipt_thumbnail_url(receipt_id: str) -> str:
    return f"/api/receipts/{receipt_id}/thumbnail"


def build_receipt_file_url(receipt_id: str) -> str:
    return f"/api/receipts/{receipt_id}/file"


def build_receipt_download_url(receipt_id: str) -> str:
    base = settings.frontend_url.rstrip("/")
    return f"{base}/api/receipts/{receipt_id}/file"
