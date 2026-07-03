from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("paperless_id", name="uq_documents_paperless_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    paperless_id: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    document_date: Mapped[date | None] = mapped_column(Date)
    document_type: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    ocr_text: Mapped[str | None] = mapped_column(Text)
    checksum: Mapped[str | None] = mapped_column(String(128))
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    paperless_url: Mapped[str | None] = mapped_column(String(1024))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    embeddings = relationship("Embedding", back_populates="document", cascade="all, delete-orphan")
    contacts = relationship("DocumentContact", back_populates="document", cascade="all, delete-orphan")
