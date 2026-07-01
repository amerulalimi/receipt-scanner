from __future__ import annotations

import re

ALLOWED_MAGIC: dict[str, bytes] = {
    "image/jpeg": bytes.fromhex("FFD8FF"),
    "image/png": bytes.fromhex("89504E47"),
    "application/pdf": bytes.fromhex("25504446"),
}

_SAFE_FILENAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def get_safe_filename(filename: str) -> str:
    """Strip path traversal and allow only safe characters."""
    base = filename.replace("\\", "/").split("/")[-1]
    sanitized = _SAFE_FILENAME_RE.sub("_", base).strip("._")
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized or "upload"


def validate_file(file_bytes: bytes, filename: str, content_type: str) -> bool:
    """Return True when magic bytes match the declared content type."""
    expected = ALLOWED_MAGIC.get(content_type)
    if expected is None:
        return False
    if len(file_bytes) < len(expected):
        return False
    if not file_bytes.startswith(expected):
        return False
    safe_name = get_safe_filename(filename)
    if not safe_name:
        return False
    return True
