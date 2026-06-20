from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.imports import ImportRequest, ImportResult
from app.services.paperless import PaperlessImporter

router = APIRouter()


@router.post("/paperless", response_model=ImportResult)
def import_paperless(payload: ImportRequest, db: Session = Depends(get_db)) -> ImportResult:
    importer = PaperlessImporter(db)
    return importer.import_documents(limit=payload.limit)
