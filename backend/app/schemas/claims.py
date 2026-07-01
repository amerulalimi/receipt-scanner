from decimal import Decimal

from pydantic import BaseModel, Field


class CategoryClaimSummary(BaseModel):
    category: str
    be_seksyen: str | None
    limit_amount: Decimal
    total_claimed: Decimal
    remaining: Decimal
    percentage: float
    receipt_count: int
    status: str
    limit: Decimal = Field(description="Backward-compatible alias for limit_amount")
    claimed: Decimal = Field(description="Backward-compatible alias for total_claimed")


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


class ReadyToFileFilingItem(BaseModel):
    be_field: str
    be_seksyen: str
    description: str
    amount_to_enter: Decimal
    receipt_count: int
    status: str


class ReadyToFileData(BaseModel):
    tax_year: int
    total_claimed: Decimal
    total_relief: Decimal
    estimated_savings: Decimal
    tax_bracket: float
    pending_review_count: int
    fields: list[ReadyToFileField]
    filing_checklist: list[ReadyToFileFilingItem]
    checklist: list[ReadyToFileChecklistItem]


class CompletenessBreakdownItem(BaseModel):
    criterion: str
    achieved: bool
    points: int


class CompletenessScoreData(BaseModel):
    tax_year: int
    score: int
    tracked_categories: int
    total_categories: int
    categories_with_claims: int
    total_claimed: Decimal
    estimated_savings: Decimal
    milestone_message: str | None = None
    next_action: str | None = None
    breakdown: list[CompletenessBreakdownItem] = Field(default_factory=list)
