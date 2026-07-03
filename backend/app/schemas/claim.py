from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ClaimDocumentRead(BaseModel):
    document_id: int | None
    filename: str | None
    event_type: str
    event_date: date | None
    amount: Decimal | None
    notes: str | None


class ClaimSummaryRead(BaseModel):
    id: int
    creditor_id: int | None
    creditor_name: str | None
    amount: Decimal | None
    currency: str
    claim_reference: str | None
    contract_reference: str | None
    title_exists: bool
    title_type: str | None
    status: str
    first_seen: date | None
    last_seen: date | None
    document_count: int
    event_count: int
    latest_document: str | None
    summary: str


class ClaimDetailRead(ClaimSummaryRead):
    documents: list[ClaimDocumentRead]
