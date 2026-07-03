from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ClaimExtractionRequest(BaseModel):
    provider: str | None = None


class ExtractedClaim(BaseModel):
    creditor_name: str | None = None
    previous_creditor_name: str | None = None
    amount: Decimal | None = None
    currency: str = "EUR"
    claim_reference: str | None = None
    contract_reference: str | None = None
    contact_name: str | None = None
    contact_organization: str | None = None
    contact_person: str | None = None
    street: str | None = None
    postal_code: str | None = None
    city: str | None = None
    country: str | None = None
    email: str | None = None
    phone: str | None = None
    title_exists: bool = False
    title_type: str | None = None
    status: str = "unknown"
    event_type: str = "document_seen"
    event_date: date | None = None
    transfer_date: date | None = None
    notes: str | None = None


class ClaimExtractionResult(BaseModel):
    document_id: int
    claim_id: int
    creditor_id: int | None
    provider: str
    model: str
    extracted: ExtractedClaim
