from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.contact import Contact, ContactAlias, DocumentContact
from app.models.document import Document


def get_or_create_contact(
    db: Session,
    *,
    display_name: str | None,
    organization_name: str | None = None,
    person_name: str | None = None,
    street: str | None = None,
    postal_code: str | None = None,
    city: str | None = None,
    country: str | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> Contact | None:
    name = _clean(display_name or organization_name or person_name)
    if not name:
        return None

    contact = db.scalar(select(Contact).where(func.lower(Contact.display_name) == name.lower()))
    if contact is None:
        alias = db.scalar(select(ContactAlias).where(func.lower(ContactAlias.alias) == name.lower()))
        contact = alias.contact if alias else None

    if contact is None:
        contact = Contact(display_name=name, country=country or "DE")
        db.add(contact)
        db.flush()
        db.add(ContactAlias(contact_id=contact.id, alias=name))

    _fill_missing(contact, "organization_name", organization_name)
    _fill_missing(contact, "person_name", person_name)
    _fill_missing(contact, "street", street)
    _fill_missing(contact, "postal_code", postal_code)
    _fill_missing(contact, "city", city)
    _fill_missing(contact, "country", country)
    _fill_missing(contact, "email", email)
    _fill_missing(contact, "phone", phone)
    return contact


def link_document_contact(
    db: Session,
    document: Document,
    contact: Contact | None,
    *,
    role: str = "unknown",
    confidence: Decimal | None = None,
) -> DocumentContact | None:
    if contact is None:
        return None
    existing = db.scalar(
        select(DocumentContact).where(
            DocumentContact.document_id == document.id,
            DocumentContact.contact_id == contact.id,
            DocumentContact.role == role,
        )
    )
    if existing:
        if confidence is not None:
            existing.confidence = confidence
        return existing
    item = DocumentContact(document_id=document.id, contact_id=contact.id, role=role, confidence=confidence)
    db.add(item)
    return item


def link_known_contacts(db: Session, document: Document) -> int:
    text = (document.ocr_text or "").lower()
    if not text:
        return 0

    linked = 0
    aliases = db.scalars(select(ContactAlias).order_by(func.length(ContactAlias.alias).desc())).all()
    for alias in aliases:
        if len(alias.alias) < 4:
            continue
        if alias.alias.lower() in text:
            link_document_contact(db, document, alias.contact, role="matched", confidence=Decimal("0.80"))
            linked += 1
    return linked


def _fill_missing(contact: Contact, field: str, value: str | None) -> None:
    cleaned = _clean(value)
    if cleaned and not getattr(contact, field):
        setattr(contact, field, cleaned)


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
