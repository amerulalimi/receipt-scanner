from __future__ import annotations

import uuid
from io import BytesIO
from pathlib import Path

from PIL import Image

from app.core.storage import (
    IMAGE_EXTENSIONS,
    get_receipt_file_path,
    get_user_upload_dir,
    thumbnail_key_for,
)


class LocalReceiptStorageBackend:
    THUMBNAIL_MAX_SIZE = 320

    def save_receipt_file(
        self,
        *,
        user_id: str,
        content: bytes,
        file_ext: str,
    ) -> str:
        file_id = uuid.uuid4()
        image_key = f"{user_id}/{file_id}.{file_ext}"
        file_path = get_receipt_file_path(image_key)
        get_user_upload_dir(user_id)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)

        normalized_ext = file_ext.lower()
        if normalized_ext in IMAGE_EXTENSIONS:
            thumb_bytes = self._generate_thumbnail(content)
            thumb_path = get_receipt_file_path(thumbnail_key_for(image_key))
            thumb_path.parent.mkdir(parents=True, exist_ok=True)
            thumb_path.write_bytes(thumb_bytes)

        return image_key

    def read_receipt_file(self, image_key: str) -> bytes | None:
        file_path = get_receipt_file_path(image_key)
        if not file_path.is_file():
            return None
        return file_path.read_bytes()

    def read_thumbnail(self, image_key: str) -> bytes | None:
        thumb_path = get_receipt_file_path(thumbnail_key_for(image_key))
        if thumb_path.is_file():
            return thumb_path.read_bytes()

        file_ext = Path(image_key).suffix.lstrip(".").lower()
        if file_ext not in IMAGE_EXTENSIONS:
            return None

        return self.read_receipt_file(image_key)

    def receipt_file_exists(self, image_key: str) -> bool:
        return get_receipt_file_path(image_key).is_file()

    def _generate_thumbnail(self, content: bytes) -> bytes:
        with Image.open(BytesIO(content)) as image:
            converted = image.convert("RGB")
            converted.thumbnail(
                (self.THUMBNAIL_MAX_SIZE, self.THUMBNAIL_MAX_SIZE),
                Image.Resampling.LANCZOS,
            )
            output = BytesIO()
            converted.save(output, format="JPEG", quality=85, optimize=True)
            return output.getvalue()


def get_local_storage_backend() -> LocalReceiptStorageBackend:
    return LocalReceiptStorageBackend()
