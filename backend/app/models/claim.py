from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
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
    transfers = relationship("ClaimTransfer", back_populates="claim", cascade="all, delete-orphan")


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


class ClaimTransfer(Base):
    __tablename__ = "claim_transfers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    claim_id: Mapped[int] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), nullable=False)
    from_creditor_id: Mapped[int | None] = mapped_column(ForeignKey("creditors.id", ondelete="SET NULL"))
    to_creditor_id: Mapped[int | None] = mapped_column(ForeignKey("creditors.id", ondelete="SET NULL"))
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    transfer_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claim = relationship("Claim", back_populates="transfers")
    from_creditor = relationship("Creditor", foreign_keys=[from_creditor_id])
    to_creditor = relationship("Creditor", foreign_keys=[to_creditor_id])
