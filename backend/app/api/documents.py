from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import DocumentDetail, DocumentList

router = APIRouter()


@router.get("", response_model=DocumentList)
def list_documents(
    db: Session = Depends(get_db),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> DocumentList:
    filters = []
    if search:
        pattern = f"%{search}%"
        filters.append(or_(Document.filename.ilike(pattern), Document.ocr_text.ilike(pattern)))

    total_query = select(func.count()).select_from(Document)
    item_query = select(Document).order_by(Document.document_date.desc().nullslast(), Document.id.desc())
    if filters:
        total_query = total_query.where(*filters)
        item_query = item_query.where(*filters)

    total = db.scalar(total_query) or 0
    items = db.scalars(item_query.limit(limit).offset(offset)).all()
    return DocumentList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
