from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class VisionLineItem(BaseModel):
    description: str = ""
    amount: Decimal = Field(default=Decimal("0"))
    kategori: str = "tidak_layak"
    claimable: bool = False


class VisionClassificationResult(BaseModel):
    merchant_name: str | None = None
    receipt_date: date | None = None
    total_amount: Decimal | None = None
    kategori: str = "semak_manual"
    seksyen: str | None = None
    jumlah_claim: Decimal | None = None
    jumlah_tidak_layak: Decimal = Field(default=Decimal("0"))
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    nota: str | None = None
    mixed_items: bool = False
    line_items: list[VisionLineItem] = Field(default_factory=list)
