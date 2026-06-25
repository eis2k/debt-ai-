from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.extraction import ClaimExtractionRequest, ClaimExtractionResult
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
        claim_id=claim.id,
        creditor_id=creditor.id if creditor else None,
        provider=provider,
        model=model,
        extracted=extracted,
    )
