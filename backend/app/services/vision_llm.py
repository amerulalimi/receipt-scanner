from __future__ import annotations

import asyncio
import base64
import json
import logging
import re

import httpx

from app.schemas.vision_llm import VisionClassificationResult

logger = logging.getLogger(__name__)

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_CATEGORIES = frozenset({"tidak_layak", "semak_manual"})

USER_PROMPT = (
    "Klasifikasikan resit cukai Malaysia ini untuk tuntutan pelepasan Borang BE. "
    "Pecahkan setiap baris item pada resit jika boleh dibaca."
)

MIME_BY_EXT = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
}


def build_system_prompt(categories: list[tuple[str, str | None]]) -> str:
    category_lines = []
    for slug, description in categories:
        label = description or slug
        category_lines.append(f"- {slug}: {label}")

    category_list = "|".join(
        [slug for slug, _ in categories] + sorted(SYSTEM_CATEGORIES),
    )
    guidance = "\n".join(category_lines) if category_lines else "- (tiada kategori aktif)"

    return f"""You are a Malaysian tax relief (Borang BE) receipt classifier.
Analyze the receipt image and return ONLY valid JSON with these fields:

{{
  "merchant_name": "string or null",
  "receipt_date": "YYYY-MM-DD or null",
  "total_amount": number or null,
  "kategori": "{category_list}",
  "seksyen": "e.g. S.46(1)(b) or null",
  "jumlah_claim": number or null,
  "jumlah_tidak_layak": number,
  "confidence": 0.0 to 1.0,
  "nota": "brief Malay explanation",
  "mixed_items": boolean,
  "line_items": [
    {{
      "description": "item name as printed on receipt",
      "amount": number,
      "kategori": "{category_list}",
      "claimable": boolean
    }}
  ]
}}

Available claim categories:
{guidance}

Rules for line_items:
- List every readable line item on the receipt (minimum 1 if items are visible).
- Set claimable=true only when the item clearly qualifies for tax relief.
- Use tidak_layak for groceries, toiletries, non-medical goods, etc.
- Set mixed_items=true when line items span more than one claim category.
- jumlah_claim should equal the sum of claimable line item amounts.
- jumlah_tidak_layak should equal the sum of non-claimable line item amounts.

Use tidak_layak if the entire receipt is clearly not claimable.
Use semak_manual if the image is unreadable or ambiguous."""


class VisionLlmService:
    def classify_receipt(
        self,
        *,
        image_bytes: bytes,
        file_type: str,
        api_key: str,
        model: str,
        categories: list[tuple[str, str | None]],
    ) -> VisionClassificationResult:
        mime = MIME_BY_EXT.get(file_type.lower(), "image/jpeg")
        data_url = f"data:{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"
        system_prompt = build_system_prompt(categories)
        allowed = frozenset(slug for slug, _ in categories) | SYSTEM_CATEGORIES

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
            "response_format": {"type": "json_object"},
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                OPENROUTER_CHAT_URL,
                headers={
                    "Authorization": f"Bearer {api_key.strip()}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

        if response.status_code == 401:
            raise RuntimeError("OpenRouter API key ditolak (401). Semak /admin/secrets.")
        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenRouter gagal ({response.status_code}): {response.text[:200]}",
            )

        body = response.json()
        content = body["choices"][0]["message"]["content"]
        if isinstance(content, list):
            text_parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            raw_text = "".join(text_parts)
        else:
            raw_text = str(content)

        return self._parse_response(raw_text, allowed)

    @staticmethod
    def _parse_response(
        raw_text: str,
        allowed_categories: frozenset[str],
    ) -> VisionClassificationResult:
        cleaned = raw_text.strip()
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned)
        if fence_match:
            cleaned = fence_match.group(1).strip()

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("Respons LLM bukan JSON sah.")

        data = json.loads(cleaned[start : end + 1])
        result = VisionClassificationResult.model_validate(data)
        if result.kategori not in allowed_categories:
            result.kategori = "semak_manual"

        normalised_items = []
        for item in result.line_items:
            category = item.kategori if item.kategori in allowed_categories else "semak_manual"
            normalised_items.append(
                item.model_copy(
                    update={
                        "kategori": category,
                        "claimable": item.claimable
                        and category not in {"tidak_layak", "semak_manual"},
                    },
                ),
            )
        result.line_items = normalised_items
        return result


async def classify_receipt_async(
    *,
    image_bytes: bytes,
    file_type: str,
    api_key: str,
    model: str,
    categories: list[tuple[str, str | None]],
) -> VisionClassificationResult:
    service = VisionLlmService()
    return await asyncio.to_thread(
        service.classify_receipt,
        image_bytes=image_bytes,
        file_type=file_type,
        api_key=api_key,
        model=model,
        categories=categories,
    )
