import pytest

from app.core.file_validator import get_safe_filename, validate_file


def test_valid_jpeg():
    content = bytes.fromhex("FFD8FF") + b"\x00" * 10
    assert validate_file(content, "photo.jpg", "image/jpeg") is True


def test_valid_png():
    content = bytes.fromhex("89504E47") + b"\x00" * 10
    assert validate_file(content, "scan.png", "image/png") is True


def test_valid_pdf():
    content = bytes.fromhex("25504446") + b"\x00" * 10
    assert validate_file(content, "bill.pdf", "application/pdf") is True


def test_invalid_magic_bytes():
    content = b"\x00\x01\x02\x03"
    assert validate_file(content, "fake.jpg", "image/jpeg") is False


def test_path_traversal_filename():
    assert ".." not in get_safe_filename("../etc/passwd")
    assert "/" not in get_safe_filename("../etc/passwd")
    assert get_safe_filename("../etc/passwd") == "passwd"


def test_safe_filename():
    assert get_safe_filename("klinik faiza (1).jpg") == "klinik_faiza_1_.jpg"
