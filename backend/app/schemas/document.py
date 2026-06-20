from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    id: int
    paperless_id: int
    filename: str
    created_at: datetime | None
    document_date: date | None
    document_type: str | None
    checksum: str | None
    confidence_score: Decimal | None
    paperless_url: str | None
    imported_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetail(DocumentRead):
    ocr_text: str | None


class DocumentList(BaseModel):
    items: list[DocumentRead]
    total: int
    limit: int
    offset: int
