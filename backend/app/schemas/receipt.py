import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ReceiptStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "flagged",
    "duplicate",
]

ReceiptScanStatus = Literal["waiting", "processing", "success", "failed"]

ReceiptFileType = Literal["jpg", "png", "pdf", "webp"]


class ReceiptCreateRequest(BaseModel):
    image_key: str = Field(min_length=1, max_length=512)
    image_hash: str = Field(min_length=64, max_length=64)
    file_name: str | None = Field(default=None, max_length=255)
    file_type: ReceiptFileType | None = None
    file_size_bytes: int | None = Field(default=None, ge=0)
    merchant_name: str | None = Field(default=None, max_length=255)
    receipt_date: date | None = None
    total_amount: Decimal = Field(gt=0, decimal_places=2)
    category: str = Field(min_length=1, max_length=50)
    claimed_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    excluded_amount: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    tax_year: int | None = Field(default=None, ge=2000, le=2100)
    ai_confidence: Decimal | None = Field(default=None, ge=0, le=1)
    ai_nota: str | None = None
    ocr_confidence: Decimal | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def set_default_claimed_amount(self):
        if self.claimed_amount is None:
            self.claimed_amount = self.total_amount
        return self


class ReceiptUpdateRequest(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=50)
    claimed_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    line_items: list["ReceiptLineItemUpdate"] | None = None
    notes: str | None = Field(default=None, max_length=2000)


class ReceiptManualCreateRequest(BaseModel):
    merchant_name: str = Field(min_length=1, max_length=255)
    receipt_date: date
    total_amount: Decimal = Field(gt=0, decimal_places=2)
    category: str = Field(min_length=1, max_length=50)
    claimed_amount: Decimal | None = Field(default=None, gt=0, decimal_places=2)
    notes: str | None = Field(default=None, max_length=2000)
    tax_year: int | None = Field(default=None, ge=2000, le=2100)


class ReceiptLineItemUpdate(BaseModel):
    id: uuid.UUID
    included_in_claim: bool
    category: str | None = Field(default=None, min_length=1, max_length=50)


class ReceiptLineItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    amount: Decimal
    category: str
    ai_claimable: bool
    included_in_claim: bool
    sort_order: int


class ReceiptReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    comment: str | None = Field(default=None, max_length=1000)


class ReceiptFlagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    flag_type: str
    message: str | None
    resolved: bool
    created_at: datetime


class ReliefStatusInfo(BaseModel):
    category: str
    be_seksyen: str | None
    limit_amount: Decimal
    total_claimed: Decimal
    remaining: Decimal
    percentage: float
    status: Literal["ok", "warning", "full"]


class ReceiptListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_name: str | None
    receipt_date: date | None
    total_amount: Decimal | None
    claimed_amount: Decimal | None
    category: str | None
    be_seksyen: str | None
    status: str
    scan_status: str
    ai_confidence: Decimal | None
    file_type: str | None
    thumbnail_url: str | None = None
    created_at: datetime


class ReceiptDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    merchant_name: str | None
    receipt_date: date | None
    total_amount: Decimal | None
    claimed_amount: Decimal | None
    excluded_amount: Decimal
    category: str | None
    be_seksyen: str | None
    status: str
    scan_status: str
    ai_confidence: Decimal | None
    ai_nota: str | None
    ocr_confidence: Decimal | None
    image_url: str | None = None
    flags: list[ReceiptFlagRead] = Field(default_factory=list)
    line_items: list[ReceiptLineItemRead] = Field(default_factory=list)
    notes: str | None = None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    relief_status: ReliefStatusInfo | None = None


class ReceiptListResponse(BaseModel):
    items: list[ReceiptListItem]
    total: int
    page: int
    limit: int


class ReceiptCreateResponse(BaseModel):
    receipt: ReceiptDetail
    relief_status: ReliefStatusInfo


class ReceiptUploadFileError(BaseModel):
    filename: str | None = None
    code: str
    message: str


class ReceiptUploadResponse(BaseModel):
    job_ids: list[uuid.UUID]
    receipt_ids: list[uuid.UUID] = Field(default_factory=list)
    message: str
    errors: list[ReceiptUploadFileError] = Field(default_factory=list)


class ReceiptDownloadData(BaseModel):
    download_url: str
    expires_in: int
    file_name: str | None = None


class ReceiptReviewResponse(BaseModel):
    receipt: ReceiptDetail
