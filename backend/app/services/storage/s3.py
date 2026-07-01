from __future__ import annotations

import asyncio
import uuid
from functools import lru_cache

import boto3
from botocore.config import Config

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.storage import ReceiptStorageBackend


class S3StorageBackend:
    """Cloudflare R2 / S3-compatible async storage (spec StorageBackend)."""

    def __init__(self) -> None:
        if not settings.r2_bucket_name:
            raise AppError(
                message="R2_BUCKET_NAME tidak dikonfigurasi.",
                code="INTERNAL_ERROR",
                status_code=501,
            )
        endpoint = (
            f"https://{settings.r2_account_id}.r2.cloudflarestorage.com"
            if settings.r2_account_id
            else None
        )
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=settings.r2_access_key_id,
            aws_secret_access_key=settings.r2_secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )
        self._bucket = settings.r2_bucket_name

    async def upload_file(self, file_bytes: bytes, key: str, content_type: str) -> str:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self._bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return key

    async def download_file(self, key: str) -> bytes:
        response = await asyncio.to_thread(
            self._client.get_object,
            Bucket=self._bucket,
            Key=key,
        )
        return await asyncio.to_thread(response["Body"].read)

    async def delete_file(self, key: str) -> None:
        await asyncio.to_thread(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )

    async def get_presigned_url(self, key: str, expires_in: int = 900) -> str:
        return await asyncio.to_thread(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )


class S3LegacyReceiptStorageAdapter(ReceiptStorageBackend):
    """Adapter for legacy ReceiptStorageBackend interface."""

    def __init__(self) -> None:
        self._s3 = S3StorageBackend()

    def save_receipt_file(
        self,
        *,
        user_id: str,
        content: bytes,
        file_ext: str,
    ) -> str:
        key = f"{user_id}/{uuid.uuid4()}.{file_ext}"
        mime = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "pdf": "application/pdf",
        }.get(file_ext.lower(), "application/octet-stream")
        asyncio.get_event_loop().run_until_complete(
            self._s3.upload_file(content, key, mime),
        )
        return key

    def read_receipt_file(self, image_key: str) -> bytes | None:
        try:
            return asyncio.get_event_loop().run_until_complete(
                self._s3.download_file(image_key),
            )
        except Exception:
            return None

    def read_thumbnail(self, image_key: str) -> bytes | None:
        return self.read_receipt_file(image_key)

    def receipt_file_exists(self, image_key: str) -> bool:
        return self.read_receipt_file(image_key) is not None


@lru_cache
def get_s3_storage_backend() -> S3StorageBackend:
    return S3StorageBackend()
