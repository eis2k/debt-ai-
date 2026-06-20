from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creditor_id: Mapped[int | None] = mapped_column(ForeignKey("creditors.id", ondelete="SET NULL"))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="EUR")
    claim_reference: Mapped[str | None] = mapped_column(String(255))
    contract_reference: Mapped[str | None] = mapped_column(String(255))
    title_exists: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    title_type: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(100), nullable=False, server_default="unknown")
    first_seen: Mapped[date | None] = mapped_column(Date)
    last_seen: Mapped[date | None] = mapped_column(Date)

    creditor = relationship("Creditor", back_populates="claims")
    events = relationship("ClaimEvent", back_populates="claim", cascade="all, delete-orphan")


class ClaimEvent(Base):
    __tablename__ = "claim_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text)

    claim = relationship("Claim", back_populates="events")
