from __future__ import annotations

from app.core.exceptions import AppError
from app.core.storage import ReceiptStorageBackend


class S3ReceiptStorageBackend(ReceiptStorageBackend):
    """Placeholder for production S3/R2 integration."""

    def save_receipt_file(
        self,
        *,
        user_id: str,
        content: bytes,
        file_ext: str,
    ) -> str:
        raise AppError(
            message="Storan S3 belum diaktifkan. Guna STORAGE_BACKEND=local untuk dev.",
            code="INTERNAL_ERROR",
            status_code=501,
        )

    def read_receipt_file(self, image_key: str) -> bytes | None:
        raise AppError(
            message="Storan S3 belum diaktifkan.",
            code="INTERNAL_ERROR",
            status_code=501,
        )

    def read_thumbnail(self, image_key: str) -> bytes | None:
        raise AppError(
            message="Storan S3 belum diaktifkan.",
            code="INTERNAL_ERROR",
            status_code=501,
        )

    def receipt_file_exists(self, image_key: str) -> bool:
        return False


def get_s3_storage_backend() -> S3ReceiptStorageBackend:
    return S3ReceiptStorageBackend()
