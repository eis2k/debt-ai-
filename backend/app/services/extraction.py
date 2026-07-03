import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil.parser import parse as parse_date
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimEvent
from app.models.creditor import Creditor, CreditorAlias
from app.models.document import Document
from app.schemas.ai import AIMessage
from app.schemas.extraction import ExtractedClaim
from app.services.ai import complete


SYSTEM_PROMPT = """Du extrahierst Forderungsdaten aus deutschen Schuldendokumenten.
Antworte ausschliesslich als JSON-Objekt ohne Markdown.
Nutze null, wenn ein Feld nicht sicher erkennbar ist.
JSON-Schema:
{
  "creditor_name": string | null,
  "amount": number | null,
  "currency": "EUR",
  "claim_reference": string | null,
  "contract_reference": string | null,
  "title_exists": boolean,
  "title_type": string | null,
  "status": "unknown" | "open" | "paid" | "disputed" | "collection" | "court",
  "event_type": "document_seen" | "invoice" | "reminder" | "collection_letter" | "court_notice" | "payment" | "other",
  "event_date": "YYYY-MM-DD" | null,
  "notes": string | null
}
"""


def extract_and_store_claim(
    db: Session,
    document: Document,
    provider: str | None = None,
) -> tuple[Claim, Creditor | None, ExtractedClaim, str, str]:
    if not document.ocr_text:
        raise ValueError("Document has no OCR text.")

    provider_name, model, content = complete(
        [
            AIMessage(role="system", content=SYSTEM_PROMPT),
            AIMessage(role="user", content=_document_prompt(document)),
        ],
        provider=provider,
        max_tokens=1200,
        temperature=0,
    )
    extracted = _parse_extraction(content)
    creditor = _get_or_create_creditor(db, extracted.creditor_name)
    claim = _get_or_create_claim(db, creditor, extracted)
    _apply_extraction_to_claim(claim, extracted, document)
    db.flush()
    _upsert_event(db, claim, document, extracted)
    db.commit()
    db.refresh(claim)
    if creditor is not None:
        db.refresh(creditor)
    return claim, creditor, extracted, provider_name, model


def _document_prompt(document: Document) -> str:
    text = document.ocr_text or ""
    return (
        f"Dateiname: {document.filename}\n"
        f"Dokumentdatum: {document.document_date.isoformat() if document.document_date else 'unbekannt'}\n\n"
        f"OCR-Text:\n{text[:12000]}"
    )


def _parse_extraction(content: str) -> ExtractedClaim:
    payload = _extract_json_object(content)
    data = json.loads(payload)
    return ExtractedClaim(
        creditor_name=_clean_string(data.get("creditor_name")),
        amount=_parse_amount(data.get("amount")),
        currency=(_clean_string(data.get("currency")) or "EUR")[:3].upper(),
        claim_reference=_clean_string(data.get("claim_reference")),
        contract_reference=_clean_string(data.get("contract_reference")),
        title_exists=bool(data.get("title_exists") or False),
        title_type=_clean_string(data.get("title_type")),
        status=_clean_status(data.get("status")),
        event_type=_clean_event_type(data.get("event_type")),
        event_date=_parse_date(data.get("event_date")),
        notes=_clean_string(data.get("notes")),
    )


def _extract_json_object(content: str) -> str:
    match = re.search(r"\{.*\}", content, flags=re.DOTALL)
    if not match:
        raise ValueError("AI response did not contain JSON.")
    return match.group(0)


def _get_or_create_creditor(db: Session, name: str | None) -> Creditor | None:
    if not name:
        return None
    creditor = db.scalar(select(Creditor).where(Creditor.canonical_name.ilike(name)))
    if creditor:
        return creditor
    alias = db.scalar(select(CreditorAlias).where(CreditorAlias.alias.ilike(name)))
    if alias:
        return alias.creditor
    creditor = Creditor(canonical_name=name)
    db.add(creditor)
    db.flush()
    db.add(CreditorAlias(creditor_id=creditor.id, alias=name))
    return creditor


def _get_or_create_claim(db: Session, creditor: Creditor | None, extracted: ExtractedClaim) -> Claim:
    filters = []
    if extracted.claim_reference:
        filters.append(Claim.claim_reference == extracted.claim_reference)
    elif creditor and extracted.contract_reference:
        filters.append(
            and_(
                Claim.creditor_id == creditor.id,
                Claim.contract_reference == extracted.contract_reference,
            )
        )

    if filters:
        claim = db.scalar(select(Claim).where(*filters))
        if claim:
            return claim

    claim = Claim(creditor_id=creditor.id if creditor else None)
    db.add(claim)
    return claim


def _apply_extraction_to_claim(claim: Claim, extracted: ExtractedClaim, document: Document) -> None:
    if extracted.amount is not None:
        claim.amount = extracted.amount
    claim.currency = extracted.currency or "EUR"
    if extracted.claim_reference:
        claim.claim_reference = extracted.claim_reference
    if extracted.contract_reference:
        claim.contract_reference = extracted.contract_reference
    claim.title_exists = extracted.title_exists
    if extracted.title_type:
        claim.title_type = extracted.title_type
    claim.status = extracted.status

    event_date = extracted.event_date or document.document_date
    if event_date:
        claim.first_seen = min([item for item in [claim.first_seen, event_date] if item])
        claim.last_seen = max([item for item in [claim.last_seen, event_date] if item])


def _upsert_event(db: Session, claim: Claim, document: Document, extracted: ExtractedClaim) -> ClaimEvent:
    event = db.scalar(
        select(ClaimEvent).where(
            ClaimEvent.claim_id == claim.id,
            ClaimEvent.document_id == document.id,
            ClaimEvent.event_type == extracted.event_type,
        )
    )
    if event is None:
        event = ClaimEvent(claim_id=claim.id, document_id=document.id, event_type=extracted.event_type)
        db.add(event)
    event.event_date = extracted.event_date or document.document_date
    event.amount = extracted.amount
    event.notes = extracted.notes
    return event


def _clean_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _parse_amount(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", ".")).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return None


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return parse_date(str(value), dayfirst=False).date()
    except (TypeError, ValueError):
        return None


def _clean_status(value: Any) -> str:
    allowed = {"unknown", "open", "paid", "disputed", "collection", "court"}
    status = (_clean_string(value) or "unknown").lower()
    return status if status in allowed else "unknown"


def _clean_event_type(value: Any) -> str:
    allowed = {"document_seen", "invoice", "reminder", "collection_letter", "court_notice", "payment", "other"}
    event_type = (_clean_string(value) or "document_seen").lower()
    return event_type if event_type in allowed else "document_seen"
