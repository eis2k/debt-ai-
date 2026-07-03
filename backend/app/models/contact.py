from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    display_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    organization_name: Mapped[str | None] = mapped_column(String(255))
    person_name: Mapped[str | None] = mapped_column(String(255))
    street: Mapped[str | None] = mapped_column(String(255))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100), nullable=False, server_default="DE")
    email: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(100))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    aliases = relationship("ContactAlias", back_populates="contact", cascade="all, delete-orphan")
    documents = relationship("DocumentContact", back_populates="contact", cascade="all, delete-orphan")
    creditors = relationship("Creditor", back_populates="contact")


class ContactAlias(Base):
    __tablename__ = "contact_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    contact = relationship("Contact", back_populates="aliases")


class DocumentContact(Base):
    __tablename__ = "document_contacts"
    __table_args__ = (UniqueConstraint("document_id", "contact_id", "role", name="uq_document_contacts_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    contact_id: Mapped[int] = mapped_column(ForeignKey("contacts.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, server_default="unknown")
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))

    document = relationship("Document", back_populates="contacts")
    contact = relationship("Contact", back_populates="documents")
