from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings
from app.core.exceptions import AppError

_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.master_encryption_key.encode())
    return _fernet


def encrypt_secret(raw_value: str) -> str:
    if not raw_value.strip():
        raise AppError(
            message="Nilai rahsia tidak boleh kosong.",
            code="VALIDATION_ERROR",
            status_code=422,
        )
    return _get_fernet().encrypt(raw_value.encode()).decode()


def decrypt_secret(encrypted_value: str) -> str:
    try:
        return _get_fernet().decrypt(encrypted_value.encode()).decode()
    except InvalidToken as exc:
        raise AppError(
            message="Gagal menyahsulit rahsia. Semak MASTER_ENCRYPTION_KEY.",
            code="INTERNAL_ERROR",
            status_code=500,
        ) from exc


def mask_secret(raw_value: str) -> str:
    if len(raw_value) <= 8:
        return "****"
    prefix = raw_value[:4] if len(raw_value) > 12 else ""
    suffix = raw_value[-4:]
    if prefix:
        return f"{prefix}****{suffix}"
    return f"****{suffix}"
