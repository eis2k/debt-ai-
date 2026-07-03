from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ClaimExtractionRequest(BaseModel):
    provider: str | None = None


class BatchClaimExtractionRequest(BaseModel):
    document_ids: list[int] | None = None
    provider: str | None = None
    limit: int = 100


class ExtractedClaim(BaseModel):
    has_claim: bool = False
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
    has_claim: bool = True
    claim_id: int | None
    creditor_id: int | None
    provider: str
    model: str
    extracted: ExtractedClaim


class BatchClaimExtractionItem(BaseModel):
    document_id: int
    filename: str
    status: str
    message: str | None = None
    result: ClaimExtractionResult | None = None


class BatchClaimExtractionResult(BaseModel):
    total: int
    processed: int
    claims_created_or_updated: int
    no_claim: int
    skipped: int
    failed: int
    items: list[BatchClaimExtractionItem]
