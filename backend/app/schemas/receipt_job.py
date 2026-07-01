import uuid

from pydantic import BaseModel, Field


class ReceiptJobPayload(BaseModel):
    job_id: str
    receipt_id: uuid.UUID
    user_id: uuid.UUID
    upload_session_token: str | None = None


class WsEventMessage(BaseModel):
    upload_session_token: str
    event: dict
