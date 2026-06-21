import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class SpouseLinkRequest(BaseModel):
    partner_email: EmailStr


class SpouseLinkRespondRequest(BaseModel):
    action: str = Field(pattern="^(accept|reject)$")


class HouseholdCategorySummary(BaseModel):
    category: str
    claimed: Decimal
    receipt_count: int


class HouseholdMemberSummary(BaseModel):
    user_id: uuid.UUID
    full_name: str | None
    email: str
    tax_year: int
    tax_bracket: float
    total_claimed: Decimal
    categories: list[HouseholdCategorySummary]


class HouseholdCombinedSummary(BaseModel):
    tax_year: int
    combined_total_claimed: Decimal
    members: list[HouseholdMemberSummary]


class SpouseIncomingRequest(BaseModel):
    id: uuid.UUID
    requester_name: str | None
    requester_email: str
    created_at: datetime


class SpouseOutgoingRequest(BaseModel):
    id: uuid.UUID
    partner_email: str
    created_at: datetime


class HouseholdOverviewData(BaseModel):
    accepted_link_id: uuid.UUID | None
    partner: HouseholdMemberSummary | None
    combined: HouseholdCombinedSummary | None
    incoming_requests: list[SpouseIncomingRequest]
    outgoing_request: SpouseOutgoingRequest | None


class ClaimSuggestionData(BaseModel):
    receipt_id: uuid.UUID
    category: str
    suggested_user_id: uuid.UUID
    reason_my: str
    reason_en: str
    user_remaining: Decimal
    spouse_remaining: Decimal


class ReceiptReassignRequest(BaseModel):
    target_user_id: uuid.UUID
