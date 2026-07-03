import json
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil.parser import parse as parse_date
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.claim import Claim, ClaimEvent, ClaimTransfer
from app.models.creditor import Creditor, CreditorAlias
from app.models.document import Document
from app.schemas.ai import AIMessage
from app.schemas.extraction import ExtractedClaim
from app.services.ai import complete
from app.services.contacts import get_or_create_contact, link_document_contact


SYSTEM_PROMPT = """Du extrahierst Forderungsdaten aus deutschen Schuldendokumenten.
Antworte ausschliesslich als JSON-Objekt ohne Markdown.
Nutze null, wenn ein Feld nicht sicher erkennbar ist.
JSON-Schema:
{
  "has_claim": boolean,
  "creditor_name": string | null,
  "previous_creditor_name": string | null,
  "amount": number | null,
  "currency": "EUR",
  "claim_reference": string | null,
  "contract_reference": string | null,
  "contact_name": string | null,
  "contact_organization": string | null,
  "contact_person": string | null,
  "street": string | null,
  "postal_code": string | null,
  "city": string | null,
  "country": string | null,
  "email": string | null,
  "phone": string | null,
  "title_exists": boolean,
  "title_type": string | null,
  "status": "unknown" | "open" | "paid" | "disputed" | "collection" | "court",
  "event_type": "document_seen" | "invoice" | "reminder" | "collection_letter" | "court_notice" | "payment" | "other",
  "event_date": "YYYY-MM-DD" | null,
  "transfer_date": "YYYY-MM-DD" | null,
  "notes": string | null
}
Setze "has_claim" nur dann auf true, wenn das Dokument tatsaechlich eine Forderung, Rechnung,
Mahnung, Inkasso-, Zahlungs- oder Gerichtsinformation enthaelt. Bei allgemeinen Briefen,
Werbung, Deckblaettern, Testdokumenten oder Dokumenten ohne Forderungsbezug setze
"has_claim": false und alle Forderungsfelder auf null beziehungsweise "unknown".
"""


def extract_and_store_claim(
    db: Session,
    document: Document,
    provider: str | None = None,
) -> tuple[Claim | None, Creditor | None, ExtractedClaim, str, str]:
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
    if not _has_meaningful_claim(extracted):
        return None, None, extracted, provider_name, model

    creditor = _get_or_create_creditor(db, extracted.creditor_name)
    contact = _get_or_create_extracted_contact(db, extracted)
    if creditor is not None and contact is not None and creditor.contact_id is None:
        creditor.contact_id = contact.id
    link_document_contact(db, document, contact, role="sender", confidence=Decimal("0.90"))
    claim = _get_or_create_claim(db, creditor, extracted)
    _record_transfer_if_needed(db, claim, creditor, document, extracted)
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
        has_claim=bool(data.get("has_claim") or False),
        creditor_name=_clean_string(data.get("creditor_name")),
        previous_creditor_name=_clean_string(data.get("previous_creditor_name")),
        amount=_parse_amount(data.get("amount")),
        currency=(_clean_string(data.get("currency")) or "EUR")[:3].upper(),
        claim_reference=_clean_string(data.get("claim_reference")),
        contract_reference=_clean_string(data.get("contract_reference")),
        contact_name=_clean_string(data.get("contact_name")),
        contact_organization=_clean_string(data.get("contact_organization")),
        contact_person=_clean_string(data.get("contact_person")),
        street=_clean_string(data.get("street")),
        postal_code=_clean_string(data.get("postal_code")),
        city=_clean_string(data.get("city")),
        country=_clean_string(data.get("country")),
        email=_clean_string(data.get("email")),
        phone=_clean_string(data.get("phone")),
        title_exists=bool(data.get("title_exists") or False),
        title_type=_clean_string(data.get("title_type")),
        status=_clean_status(data.get("status")),
        event_type=_clean_event_type(data.get("event_type")),
        event_date=_parse_date(data.get("event_date")),
        transfer_date=_parse_date(data.get("transfer_date")),
        notes=_clean_string(data.get("notes")),
    )


def _has_meaningful_claim(extracted: ExtractedClaim) -> bool:
    if not extracted.has_claim:
        return False
    return any(
        [
            extracted.creditor_name,
            extracted.amount is not None,
            extracted.claim_reference,
            extracted.contract_reference,
            extracted.previous_creditor_name,
            extracted.title_exists,
            extracted.event_type in {"invoice", "reminder", "collection_letter", "court_notice", "payment"},
        ]
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


def _get_or_create_extracted_contact(db: Session, extracted: ExtractedClaim):
    return get_or_create_contact(
        db,
        display_name=extracted.contact_name or extracted.contact_organization or extracted.creditor_name,
        organization_name=extracted.contact_organization or extracted.creditor_name,
        person_name=extracted.contact_person,
        street=extracted.street,
        postal_code=extracted.postal_code,
        city=extracted.city,
        country=extracted.country or "DE",
        email=extracted.email,
        phone=extracted.phone,
    )


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
    if extracted.creditor_name:
        creditor_id = claim.creditor_id
    else:
        creditor_id = None
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
    if creditor_id:
        claim.creditor_id = creditor_id

    event_date = extracted.event_date or document.document_date
    if event_date:
        claim.first_seen = min([item for item in [claim.first_seen, event_date] if item])
        claim.last_seen = max([item for item in [claim.last_seen, event_date] if item])


def _record_transfer_if_needed(
    db: Session,
    claim: Claim,
    creditor: Creditor | None,
    document: Document,
    extracted: ExtractedClaim,
) -> ClaimTransfer | None:
    if creditor is None:
        return None
    if claim.creditor_id is None:
        claim.creditor_id = creditor.id
        return None
    if claim.creditor_id == creditor.id:
        return None

    existing = db.scalar(
        select(ClaimTransfer).where(
            ClaimTransfer.claim_id == claim.id,
            ClaimTransfer.from_creditor_id == claim.creditor_id,
            ClaimTransfer.to_creditor_id == creditor.id,
            ClaimTransfer.document_id == document.id,
        )
    )
    if existing:
        claim.creditor_id = creditor.id
        return existing

    transfer = ClaimTransfer(
        claim_id=claim.id,
        from_creditor_id=claim.creditor_id,
        to_creditor_id=creditor.id,
        document_id=document.id,
        transfer_date=extracted.transfer_date or extracted.event_date or document.document_date,
        notes=extracted.notes or f"Forderung wechselte zu {creditor.canonical_name}.",
    )
    db.add(transfer)
    claim.creditor_id = creditor.id
    return transfer


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
