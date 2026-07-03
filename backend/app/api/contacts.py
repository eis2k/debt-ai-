from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.contact import Contact, ContactAlias, DocumentContact
from app.models.creditor import Creditor
from app.models.document import Document
from app.schemas.contact import ContactDetail, ContactSummary

router = APIRouter()


@router.get("", response_model=list[ContactSummary])
def list_contacts(db: Session = Depends(get_db)) -> list[ContactSummary]:
    rows = db.execute(
        select(
            Contact,
            func.count(func.distinct(DocumentContact.document_id)).label("document_count"),
            func.count(func.distinct(Creditor.id)).label("creditor_count"),
        )
        .outerjoin(DocumentContact, DocumentContact.contact_id == Contact.id)
        .outerjoin(Creditor, Creditor.contact_id == Contact.id)
        .group_by(Contact.id)
        .order_by(Contact.display_name)
    ).all()
    return [
        ContactSummary(
            id=contact.id,
            display_name=contact.display_name,
            organization_name=contact.organization_name,
            person_name=contact.person_name,
            street=contact.street,
            postal_code=contact.postal_code,
            city=contact.city,
            country=contact.country,
            email=contact.email,
            phone=contact.phone,
            document_count=document_count,
            creditor_count=creditor_count,
            created_at=contact.created_at,
            updated_at=contact.updated_at,
        )
        for contact, document_count, creditor_count in rows
    ]


@router.get("/{contact_id}", response_model=ContactDetail)
def get_contact(contact_id: int, db: Session = Depends(get_db)) -> ContactDetail:
    contact = db.get(Contact, contact_id)
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    aliases = db.scalars(select(ContactAlias.alias).where(ContactAlias.contact_id == contact_id).order_by(ContactAlias.alias)).all()
    documents = db.execute(
        select(Document.id, Document.filename, Document.document_date, DocumentContact.role)
        .join(DocumentContact, DocumentContact.document_id == Document.id)
        .where(DocumentContact.contact_id == contact_id)
        .order_by(Document.document_date.desc().nullslast(), Document.id.desc())
    ).all()
    return ContactDetail(
        id=contact.id,
        display_name=contact.display_name,
        organization_name=contact.organization_name,
        person_name=contact.person_name,
        street=contact.street,
        postal_code=contact.postal_code,
        city=contact.city,
        country=contact.country,
        email=contact.email,
        phone=contact.phone,
        notes=contact.notes,
        aliases=list(aliases),
        documents=[
            {"id": document_id, "filename": filename, "document_date": document_date, "role": role}
            for document_id, filename, document_date, role in documents
        ],
    )
