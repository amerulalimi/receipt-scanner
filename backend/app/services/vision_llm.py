from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.repositories.system_config import SystemConfigRepository
from app.schemas.vision_llm import VisionClassificationResult, VisionLineItem
from app.services.job_queue import get_openrouter_credentials

logger = logging.getLogger(__name__)

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

SPEC_CATEGORIES = (
    "perubatan|gaya_hidup|sukan|pendidikan|sspn|ev_charging|tidak_layak"
)

SYSTEM_PROMPT = f"""You are a Malaysian tax receipt classifier for Borang BE.
Extract information from this receipt image and respond ONLY with valid JSON.

Required fields:
{{
  "merchant_name": "string or null",
  "receipt_date": "YYYY-MM-DD or null",
  "total_amount": number or null,
  "ocr_confidence": 0.0-1.0,
  "category": "{SPEC_CATEGORIES}",
  "be_seksyen": "e.g. S.46(1)(b) or null",
  "claimed_amount": number or null,
  "excluded_amount": 0,
  "ai_confidence": 0.0-1.0,
  "ai_nota": "brief explanation in Bahasa Malaysia",
  "is_mixed": boolean,
  "line_items": [
    {{
      "description": "string",
      "amount": number,
      "category": "{SPEC_CATEGORIES}",
      "ai_claimable": boolean
    }}
  ]
}}

Rules:
- line_items only if is_mixed is true (pharmacy with mixed items, etc.)
- If cannot read receipt clearly, set ocr_confidence < 0.7
- category must be one of the exact values listed
- All amounts in MYR"""

MIME_BY_EXT = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "pdf": "application/pdf",
}

PDF_MANUAL_REVIEW = {
    "scan_status": "failed",
    "flags": ["manual_review"],
    "ai_nota": "PDF tidak disokong untuk OCR automatik. Sila masukkan secara manual.",
}


async def resolve_vision_model(db: AsyncSession | None, model: str | None = None) -> str:
    if model:
        return model
    if db is not None:
        config = SystemConfigRepository(db)
        item = await config.get_by_key("openrouter_vision_model")
        if item and item.value:
            return item.value
    return settings.openrouter_vision_model


async def classify_receipt(
    image_bytes: bytes,
    file_type: str,
    *,
    db: AsyncSession | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Classify a receipt image via OpenRouter. Returns spec-shaped dict including scan_status.
  PDF files skip the API and return manual_review stub.
    """
    normalized_type = file_type.lower().lstrip(".")

    if normalized_type == "pdf":
        return {**PDF_MANUAL_REVIEW, "category": "tidak_layak"}

    resolved_model = await resolve_vision_model(db, model)
    resolved_key = api_key
    if resolved_key is None and db is not None:
        credentials = await get_openrouter_credentials(db)
        if credentials is None:
            return _failed_result("OpenRouter API key tidak dikonfigurasi.")
        resolved_key, resolved_model = credentials
    elif resolved_key is None:
        resolved_key = settings.openrouter_api_key
        if not resolved_key:
            return _failed_result("OpenRouter API key tidak dikonfigurasi.")

    mime = MIME_BY_EXT.get(normalized_type, "image/jpeg")
    data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"

    payload = {
        "model": resolved_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                    {
                        "type": "text",
                        "text": "Klasifikasikan resit ini.",
                    },
                ],
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 1000,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                OPENROUTER_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {resolved_key.strip()}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code >= 400:
            logger.warning("OpenRouter error %s: %s", response.status_code, response.text[:200])
            return _failed_result(f"OpenRouter gagal ({response.status_code}).")

        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, list):
            raw_text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
        else:
            raw_text = str(content)

        parsed = _parse_json_response(raw_text)
        parsed["scan_status"] = "success"
        return parsed
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.warning("Failed to parse OpenRouter response: %s", exc)
        return _failed_result("Respons AI tidak sah.")
    except Exception as exc:
        logger.exception("OpenRouter request failed")
        return _failed_result(str(exc)[:200])


def _failed_result(message: str) -> dict[str, Any]:
    return {
        "scan_status": "failed",
        "flags": ["manual_review"],
        "ai_nota": message,
        "category": "tidak_layak",
        "ocr_confidence": 0.0,
        "ai_confidence": 0.0,
    }


def _parse_json_response(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Respons LLM bukan JSON sah.")

    data = json.loads(cleaned[start : end + 1])
    receipt_date = data.get("receipt_date")
    if receipt_date == "":
        receipt_date = None

    line_items = []
    for item in data.get("line_items") or []:
        line_items.append(
            {
                "description": str(item.get("description") or ""),
                "amount": item.get("amount"),
                "category": item.get("category") or "tidak_layak",
                "ai_claimable": bool(item.get("ai_claimable", False)),
            },
        )

    return {
        "merchant_name": data.get("merchant_name"),
        "receipt_date": receipt_date,
        "total_amount": data.get("total_amount"),
        "ocr_confidence": float(data.get("ocr_confidence") or 0.0),
        "category": data.get("category") or "tidak_layak",
        "be_seksyen": data.get("be_seksyen"),
        "claimed_amount": data.get("claimed_amount"),
        "excluded_amount": data.get("excluded_amount") or 0,
        "ai_confidence": float(data.get("ai_confidence") or data.get("ocr_confidence") or 0.0),
        "ai_nota": data.get("ai_nota"),
        "is_mixed": bool(data.get("is_mixed", False)),
        "line_items": line_items,
        "flags": [],
        "ocr_raw": data,
    }


def spec_result_to_vision_model(result: dict[str, Any]) -> VisionClassificationResult:
    """Map spec-shaped classify_receipt output to legacy VisionClassificationResult."""
    line_items = [
        VisionLineItem(
            description=item.get("description", ""),
            amount=Decimal(str(item.get("amount") or 0)),
            kategori=item.get("category", "tidak_layak"),
            claimable=bool(item.get("ai_claimable", False)),
        )
        for item in result.get("line_items") or []
    ]
    ocr_conf = float(result.get("ocr_confidence") or 0.0)
    ai_conf = float(result.get("ai_confidence") or ocr_conf)
    return VisionClassificationResult(
        merchant_name=result.get("merchant_name"),
        receipt_date=_parse_date(result.get("receipt_date")),
        total_amount=_optional_decimal(result.get("total_amount")),
        kategori=result.get("category") or "tidak_layak",
        seksyen=result.get("be_seksyen"),
        jumlah_claim=_optional_decimal(result.get("claimed_amount")),
        jumlah_tidak_layak=Decimal(str(result.get("excluded_amount") or 0)),
        confidence=ai_conf,
        nota=result.get("ai_nota"),
        mixed_items=bool(result.get("is_mixed", False)),
        line_items=line_items,
    )


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _optional_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


async def classify_receipt_async(
    *,
    image_bytes: bytes,
    file_type: str,
    api_key: str,
    model: str,
    categories: list[tuple[str, str | None]],
) -> VisionClassificationResult:
    """Backward-compatible wrapper used by worker paths."""
    del categories
    result = await classify_receipt(
        image_bytes,
        file_type,
        api_key=api_key,
        model=model,
    )
    return spec_result_to_vision_model(result)
