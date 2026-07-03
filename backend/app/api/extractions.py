from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.extraction import (
    BatchClaimExtractionItem,
    BatchClaimExtractionRequest,
    BatchClaimExtractionResult,
    ClaimExtractionRequest,
    ClaimExtractionResult,
)
from app.services.ai import AIProviderError
from app.services.extraction import extract_and_store_claim

router = APIRouter()


@router.post("/documents/{document_id}/claim", response_model=ClaimExtractionResult)
def extract_claim_from_document(
    document_id: int,
    payload: ClaimExtractionRequest,
    db: Session = Depends(get_db),
) -> ClaimExtractionResult:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        claim, creditor, extracted, provider, model = extract_and_store_claim(db, document, provider=payload.provider)
    except AIProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ClaimExtractionResult(
        document_id=document.id,
        has_claim=claim is not None,
        claim_id=claim.id if claim else None,
        creditor_id=creditor.id if creditor else None,
        provider=provider,
        model=model,
        extracted=extracted,
    )


@router.post("/claims/batch", response_model=BatchClaimExtractionResult)
def extract_claims_batch(
    payload: BatchClaimExtractionRequest,
    db: Session = Depends(get_db),
) -> BatchClaimExtractionResult:
    documents = _batch_documents(db, payload)
    items: list[BatchClaimExtractionItem] = []
    claims_count = 0
    no_claim_count = 0
    skipped_count = 0
    failed_count = 0

    for document in documents:
        if not document.ocr_text:
            skipped_count += 1
            items.append(
                BatchClaimExtractionItem(
                    document_id=document.id,
                    filename=document.filename,
                    status="skipped",
                    message="Kein OCR-Text vorhanden.",
                )
            )
            continue

        try:
            claim, creditor, extracted, provider, model = extract_and_store_claim(db, document, provider=payload.provider)
        except (AIProviderError, ValueError) as exc:
            db.rollback()
            failed_count += 1
            items.append(
                BatchClaimExtractionItem(
                    document_id=document.id,
                    filename=document.filename,
                    status="failed",
                    message=str(exc),
                )
            )
            continue

        result = ClaimExtractionResult(
            document_id=document.id,
            has_claim=claim is not None,
            claim_id=claim.id if claim else None,
            creditor_id=creditor.id if creditor else None,
            provider=provider,
            model=model,
            extracted=extracted,
        )
        if claim is None:
            no_claim_count += 1
            status = "no_claim"
            message = "Keine Forderung erkannt."
        else:
            claims_count += 1
            status = "claim"
            message = "Forderung gespeichert."
        items.append(
            BatchClaimExtractionItem(
                document_id=document.id,
                filename=document.filename,
                status=status,
                message=message,
                result=result,
            )
        )

    return BatchClaimExtractionResult(
        total=len(documents),
        processed=len(items),
        claims_created_or_updated=claims_count,
        no_claim=no_claim_count,
        skipped=skipped_count,
        failed=failed_count,
        items=items,
    )


def _batch_documents(db: Session, payload: BatchClaimExtractionRequest) -> list[Document]:
    limit = max(1, min(payload.limit, 500))
    if payload.document_ids:
        ids = payload.document_ids[:limit]
        rows = db.scalars(select(Document).where(Document.id.in_(ids)).order_by(Document.imported_at.desc())).all()
        by_id = {document.id: document for document in rows}
        return [by_id[document_id] for document_id in ids if document_id in by_id]
    return list(db.scalars(select(Document).order_by(Document.imported_at.desc()).limit(limit)).all())
