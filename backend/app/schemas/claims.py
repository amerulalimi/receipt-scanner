import uuid
from decimal import Decimal

from pydantic import BaseModel


class CategoryClaimSummary(BaseModel):
    category: str
    be_seksyen: str | None
    limit: Decimal
    claimed: Decimal
    remaining: Decimal
    percentage: float
    receipt_count: int
    status: str


class ClaimSummaryData(BaseModel):
    tax_year: int
    tax_bracket: float
    estimated_savings: Decimal
    categories: list[CategoryClaimSummary]


class ClaimCompareData(BaseModel):
    current_year: int
    previous_year: int
    current: ClaimSummaryData
    previous: ClaimSummaryData


class ReadyToFileField(BaseModel):
    step: int
    category: str
    be_seksyen: str
    lhdn_section: str
    lhdn_field_my: str
    lhdn_field_en: str
    amount: Decimal
    receipt_count: int


class ReadyToFileChecklistItem(BaseModel):
    order: int
    text_my: str
    text_en: str


class ReadyToFileData(BaseModel):
    tax_year: int
    total_claimed: Decimal
    estimated_savings: Decimal
    tax_bracket: float
    pending_review_count: int
    fields: list[ReadyToFileField]
    checklist: list[ReadyToFileChecklistItem]


class CompletenessScoreData(BaseModel):
    tax_year: int
    score: int
    tracked_categories: int
    total_categories: int
    categories_with_claims: int
    total_claimed: Decimal
    estimated_savings: Decimal
    milestone_message: str | None = None
