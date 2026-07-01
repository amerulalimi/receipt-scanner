from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.storage import MIME_BY_FILE_TYPE
from app.models.receipt import Receipt
from app.models.receipt_flag import ReceiptFlag
from app.repositories.receipt import ReceiptRepository
from app.repositories.receipt_line_item import ReceiptLineItemRepository
from app.services.dedup import (
    check_duplicate,
    compute_hash,
    derive_duplicate_image_hash,
)
from app.services.rule_engine import apply_rules
from app.services.storage import build_receipt_storage_key, get_storage, save_receipt_via_legacy_local
from app.services.tax_year import tax_year_from_receipt_date
from app.services.vision_llm import classify_receipt

FLAG_MESSAGES = {
    "low_ocr_confidence": "Keyakinan OCR rendah.",
    "low_ai_confidence": "Keyakinan AI rendah.",
    "mixed_items": "Resit mengandungi item campuran.",
    "limit_exceeded": "Tuntutan melebihi had pelepasan.",
    "duplicate_suspected": "Imej yang sama telah dimuat naik sebelum ini.",
    "manual_review": "Resit memerlukan semakan manual.",
}


async def process_receipt(
    db: AsyncSession,
    redis: Redis | None,
    storage,
    user_id: uuid.UUID,
    org_id: uuid.UUID | None,
    tax_year: int,
    file_bytes: bytes,
    file_name: str | None,
    file_type: str,
    file_size: int,
) -> Receipt:
    """
    Synchronous Phase 2 pipeline: hash → dedup → storage → classify → rules → persist.
    """
    del redis
    repo = ReceiptRepository(db)
    content_hash = await compute_hash(file_bytes)
    existing = await check_duplicate(db, content_hash, user_id)

    if existing is not None:
        return await _create_duplicate_receipt(
            db,
            repo=repo,
            user_id=user_id,
            org_id=org_id,
            tax_year=tax_year,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            content_hash=content_hash,
            original=existing,
        )

    normalized_type = file_type.lower().lstrip(".")
    backend_name = settings.storage_backend.strip().lower()

    if backend_name in {"s3", "r2"}:
        storage_key = build_receipt_storage_key(user_id, normalized_type)
        content_type = MIME_BY_FILE_TYPE.get(normalized_type, "application/octet-stream")
        active_storage = storage if storage is not None else get_storage()
        storage_key = await active_storage.upload_file(file_bytes, storage_key, content_type)
    else:
        storage_key = save_receipt_via_legacy_local(
            user_id=str(user_id),
            content=file_bytes,
            file_ext=normalized_type,
        )

    receipt = Receipt(
        user_id=user_id,
        org_id=org_id,
        tax_year=tax_year,
        image_key=storage_key,
        image_hash=content_hash,
        file_name=file_name,
        file_type=normalized_type,
        file_size_bytes=file_size,
        category="tidak_layak",
        status="pending",
        scan_status="processing",
    )
    receipt = await repo.create_receipt(receipt)

    if normalized_type == "pdf":
        ai_result = {
            "scan_status": "failed",
            "flags": ["manual_review"],
            "ai_nota": "PDF tidak disokong untuk OCR automatik. Sila masukkan secara manual.",
            "category": "tidak_layak",
        }
    else:
        ai_result = await classify_receipt(file_bytes, normalized_type, db=db)
    scan_status = ai_result.get("scan_status", "failed")

    if scan_status == "failed" and normalized_type == "pdf":
        receipt.scan_status = "failed"
        receipt.status = "pending"
        receipt.category = "tidak_layak"
        receipt.ai_nota = ai_result.get("ai_nota")
        await _add_flags(db, receipt, ai_result.get("flags") or ["manual_review"])
        await db.flush()
        return receipt

    if scan_status == "failed":
        receipt.scan_status = "failed"
        receipt.status = "flagged"
        receipt.category = ai_result.get("category") or "tidak_layak"
        receipt.ai_nota = ai_result.get("ai_nota")
        await _add_flags(db, receipt, ai_result.get("flags") or ["manual_review"])
        await db.flush()
        return receipt

    resolved_tax_year = tax_year_from_receipt_date(
        _parse_date(ai_result.get("receipt_date")),
        tax_year,
    )
    rules = await apply_rules(
        db,
        user_id,
        resolved_tax_year,
        ai_result,
    )

    receipt.tax_year = resolved_tax_year
    receipt.merchant_name = ai_result.get("merchant_name")
    receipt.receipt_date = _parse_date(ai_result.get("receipt_date"))
    receipt.total_amount = _decimal_or_none(ai_result.get("total_amount"))
    receipt.category = rules["category"]
    receipt.be_seksyen = rules.get("be_seksyen")
    receipt.claimed_amount = rules["claimed_amount"]
    receipt.excluded_amount = Decimal(str(ai_result.get("excluded_amount") or 0))
    receipt.ocr_confidence = Decimal(str(round(float(rules.get("ocr_confidence", 0)), 3)))
    receipt.ai_confidence = Decimal(str(round(float(rules.get("ai_confidence", 0)), 3)))
    receipt.ai_nota = rules.get("ai_nota") or ai_result.get("ai_nota")
    receipt.ocr_raw = ai_result.get("ocr_raw")
    receipt.scan_status = "success"
    receipt.status = "flagged" if rules["flags"] else "pending"

    line_items = ai_result.get("line_items") or []
    if ai_result.get("is_mixed") and line_items:
        line_repo = ReceiptLineItemRepository(db)
        await line_repo.delete_for_receipt(receipt.id)
        await line_repo.create_many(
            receipt.id,
            [
                {
                    "description": str(item.get("description", ""))[:500],
                    "amount": item.get("amount") or 0,
                    "category": item.get("category") or rules["category"],
                    "ai_claimable": bool(item.get("ai_claimable", False)),
                    "included_in_claim": bool(item.get("ai_claimable", False)),
                }
                for item in line_items
            ],
        )

    await _add_flags(db, receipt, rules["flags"])
    await db.flush()
    return receipt


async def _create_duplicate_receipt(
    db: AsyncSession,
    *,
    repo: ReceiptRepository,
    user_id: uuid.UUID,
    org_id: uuid.UUID | None,
    tax_year: int,
    file_name: str | None,
    file_type: str,
    file_size: int,
    content_hash: str,
    original: Receipt,
) -> Receipt:
    normalized_type = file_type.lower().lstrip(".")
    from io import BytesIO

    from PIL import Image

    placeholder = Image.new("RGB", (2, 2), color="white")
    buffer = BytesIO()
    placeholder.save(buffer, format="PNG")
    tiny_png = buffer.getvalue()
    placeholder_key = save_receipt_via_legacy_local(
        user_id=str(user_id),
        content=tiny_png,
        file_ext="png",
    )
    receipt = Receipt(
        user_id=user_id,
        org_id=org_id,
        tax_year=tax_year,
        image_key=placeholder_key,
        image_hash=derive_duplicate_image_hash(content_hash),
        file_name=file_name,
        file_type=normalized_type,
        file_size_bytes=file_size,
        category=original.category,
        status="duplicate",
        scan_status="failed",
        merchant_name=original.merchant_name,
        total_amount=original.total_amount,
        claimed_amount=original.claimed_amount,
    )
    receipt = await repo.create_receipt(receipt)
    await repo.create_flag(
        receipt.id,
        "duplicate_suspected",
        f"Duplikat resit asal: {original.id}",
    )
    await db.flush()
    return receipt


async def _add_flags(
    db: AsyncSession,
    receipt: Receipt,
    flag_types: list[str],
) -> None:
    repo = ReceiptRepository(db)
    for flag_type in flag_types:
        await repo.create_flag(
            receipt.id,
            flag_type,
            FLAG_MESSAGES.get(flag_type, flag_type),
        )


def _parse_date(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _decimal_or_none(value) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))
