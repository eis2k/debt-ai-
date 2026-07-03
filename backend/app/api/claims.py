from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim, ClaimEvent
from app.models.creditor import Creditor
from app.models.document import Document
from app.schemas.claim import ClaimDetailRead, ClaimDocumentRead, ClaimSummaryRead

router = APIRouter()


@router.get("", response_model=list[ClaimSummaryRead])
def list_claims(db: Session = Depends(get_db)) -> list[ClaimSummaryRead]:
    rows = db.execute(
        select(
            Claim,
            Creditor.canonical_name,
            func.count(ClaimEvent.id).label("event_count"),
            func.count(func.distinct(ClaimEvent.document_id)).label("document_count"),
        )
        .outerjoin(Creditor, Creditor.id == Claim.creditor_id)
        .outerjoin(ClaimEvent, ClaimEvent.claim_id == Claim.id)
        .group_by(Claim.id, Creditor.canonical_name)
        .order_by(Claim.last_seen.desc().nullslast(), Claim.id.desc())
    ).all()
    return [
        _summary_read(
            db,
            claim=claim,
            creditor_name=creditor_name,
            event_count=int(event_count or 0),
            document_count=int(document_count or 0),
        )
        for claim, creditor_name, event_count, document_count in rows
    ]


@router.get("/{claim_id}", response_model=ClaimDetailRead)
def get_claim(claim_id: int, db: Session = Depends(get_db)) -> ClaimDetailRead:
    row = db.execute(
        select(Claim, Creditor.canonical_name)
        .outerjoin(Creditor, Creditor.id == Claim.creditor_id)
        .where(Claim.id == claim_id)
    ).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    claim, creditor_name = row
    documents = _claim_documents(db, claim.id)
    summary = _summary_read(
        db,
        claim=claim,
        creditor_name=creditor_name,
        event_count=len(documents),
        document_count=len({item.document_id for item in documents if item.document_id is not None}),
    )
    return ClaimDetailRead(**summary.model_dump(), documents=documents)


def _summary_read(
    db: Session,
    *,
    claim: Claim,
    creditor_name: str | None,
    event_count: int,
    document_count: int,
) -> ClaimSummaryRead:
    latest_document = db.execute(
        select(Document.filename)
        .join(ClaimEvent, ClaimEvent.document_id == Document.id)
        .where(ClaimEvent.claim_id == claim.id)
        .order_by(ClaimEvent.event_date.desc().nullslast(), ClaimEvent.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    return ClaimSummaryRead(
        id=claim.id,
        creditor_id=claim.creditor_id,
        creditor_name=creditor_name,
        amount=claim.amount,
        currency=claim.currency,
        claim_reference=claim.claim_reference,
        contract_reference=claim.contract_reference,
        title_exists=claim.title_exists,
        title_type=claim.title_type,
        status=claim.status,
        first_seen=claim.first_seen,
        last_seen=claim.last_seen,
        document_count=document_count,
        event_count=event_count,
        latest_document=latest_document,
        summary=_claim_summary_text(claim, creditor_name, document_count),
    )


def _claim_documents(db: Session, claim_id: int) -> list[ClaimDocumentRead]:
    rows = db.execute(
        select(ClaimEvent, Document.filename)
        .outerjoin(Document, Document.id == ClaimEvent.document_id)
        .where(ClaimEvent.claim_id == claim_id)
        .order_by(ClaimEvent.event_date.asc().nullslast(), ClaimEvent.id.asc())
    ).all()
    return [
        ClaimDocumentRead(
            document_id=event.document_id,
            filename=filename,
            event_type=event.event_type,
            event_date=event.event_date,
            amount=event.amount,
            notes=event.notes,
        )
        for event, filename in rows
    ]


def _claim_summary_text(claim: Claim, creditor_name: str | None, document_count: int) -> str:
    parts: list[str] = []
    if creditor_name:
        parts.append(f"Glaeubiger: {creditor_name}")
    if claim.amount is not None:
        parts.append(f"Betrag: {_format_amount(claim.amount)} {claim.currency}")
    if claim.claim_reference:
        parts.append(f"Aktenzeichen: {claim.claim_reference}")
    if claim.contract_reference:
        parts.append(f"Vertrag: {claim.contract_reference}")
    if claim.first_seen or claim.last_seen:
        parts.append(f"Zeitraum: {claim.first_seen or '?'} bis {claim.last_seen or '?'}")
    if claim.title_exists:
        parts.append(f"Titel: {claim.title_type or 'vorhanden'}")
    parts.append(f"Schreiben: {document_count}")
    parts.append(f"Status: {claim.status}")
    return " | ".join(parts)


def _format_amount(value: Decimal) -> str:
    return f"{value:.2f}".replace(".", ",")
