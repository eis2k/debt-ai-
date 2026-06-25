from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ClaimExtractionRequest(BaseModel):
    provider: str | None = None


class ExtractedClaim(BaseModel):
    creditor_name: str | None = None
    amount: Decimal | None = None
    currency: str = "EUR"
    claim_reference: str | None = None
    contract_reference: str | None = None
    title_exists: bool = False
    title_type: str | None = None
    status: str = "unknown"
    event_type: str = "document_seen"
    event_date: date | None = None
    notes: str | None = None


class ClaimExtractionResult(BaseModel):
    document_id: int
    claim_id: int
    creditor_id: int | None
    provider: str
    model: str
    extracted: ExtractedClaim
