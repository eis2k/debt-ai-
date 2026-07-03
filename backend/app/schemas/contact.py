from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ContactSummary(BaseModel):
    id: int
    display_name: str
    organization_name: str | None
    person_name: str | None
    street: str | None
    postal_code: str | None
    city: str | None
    country: str
    email: str | None
    phone: str | None
    document_count: int
    creditor_count: int
    created_at: datetime
    updated_at: datetime


class ContactDetail(BaseModel):
    id: int
    display_name: str
    organization_name: str | None
    person_name: str | None
    street: str | None
    postal_code: str | None
    city: str | None
    country: str
    email: str | None
    phone: str | None
    notes: str | None
    aliases: list[str]
    documents: list[dict]

    model_config = ConfigDict(from_attributes=True)


class DocumentContactRead(BaseModel):
    document_id: int
    contact_id: int
    role: str
    confidence: Decimal | None
