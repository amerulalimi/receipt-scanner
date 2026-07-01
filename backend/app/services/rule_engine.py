from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.claim_limit import NON_CLAIMABLE_CATEGORIES, ClaimLimitService
from app.services.relief_limits_cache import get_active_relief_limits

LOW_OCR_CONFIDENCE = 0.70
LOW_AI_CONFIDENCE = 0.70


async def apply_rules(
    db: AsyncSession,
    user_id: uuid.UUID,
    tax_year: int,
    ai_result: dict[str, Any],
    redis: Redis | None = None,
) -> dict[str, Any]:
    """
    Apply relief-limit and confidence rules to AI classification output.

    Returns dict with claimed_amount, flags, category, be_seksyen, limit_remaining.
    """
    claim_limits = ClaimLimitService(db)
    active_limits = await get_active_relief_limits(db, redis)
    active_categories = {item.category for item in active_limits}
    limit_by_category = {item.category: item for item in active_limits}

    category = str(ai_result.get("category") or "tidak_layak")
    if category not in active_categories and category not in NON_CLAIMABLE_CATEGORIES:
        category = "tidak_layak"
        ai_result["category"] = category

    claimed_amount = _to_decimal(ai_result.get("claimed_amount"))
    ocr_confidence = float(ai_result.get("ocr_confidence") or 0.0)
    ai_confidence = float(ai_result.get("ai_confidence") or ocr_confidence)
    is_mixed = bool(ai_result.get("is_mixed", False))
    ai_nota = str(ai_result.get("ai_nota") or "")
    flags: list[str] = list(ai_result.get("flags") or [])

    be_seksyen = ai_result.get("be_seksyen")
    if not be_seksyen and category in limit_by_category:
        be_seksyen = limit_by_category[category].be_seksyen

    limit_remaining = Decimal("0")

    if category not in NON_CLAIMABLE_CATEGORIES:
        relief = limit_by_category.get(category)
        if relief is not None:
            check = await claim_limits.check_claim(
                user_id=user_id,
                tax_year=tax_year,
                category=category,
                new_claimed_amount=claimed_amount,
                raise_on_exceed=False,
            )
            limit_remaining = check.relief_status.remaining
            if check.would_exceed:
                claimed_amount = limit_remaining
                if "limit_exceeded" not in flags:
                    flags.append("limit_exceeded")
                ai_nota = (
                    f"{ai_nota} Had pelepasan untuk kategori ini telah dicapai.".strip()
                )

    if ocr_confidence < LOW_OCR_CONFIDENCE and "low_ocr_confidence" not in flags:
        flags.append("low_ocr_confidence")

    if ai_confidence < LOW_AI_CONFIDENCE and "low_ai_confidence" not in flags:
        flags.append("low_ai_confidence")

    if is_mixed and "mixed_items" not in flags:
        flags.append("mixed_items")

    return {
        "claimed_amount": claimed_amount,
        "flags": flags,
        "category": category,
        "be_seksyen": be_seksyen,
        "limit_remaining": limit_remaining,
        "ai_nota": ai_nota,
        "ocr_confidence": ocr_confidence,
        "ai_confidence": ai_confidence,
    }


def _to_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))
