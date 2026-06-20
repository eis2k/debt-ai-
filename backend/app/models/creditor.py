from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Creditor(Base):
    __tablename__ = "creditors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    notes: Mapped[str | None] = mapped_column(Text)

    aliases = relationship("CreditorAlias", back_populates="creditor", cascade="all, delete-orphan")
    claims = relationship("Claim", back_populates="creditor")


class CreditorAlias(Base):
    __tablename__ = "creditor_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    creditor_id: Mapped[int] = mapped_column(ForeignKey("creditors.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    creditor = relationship("Creditor", back_populates="aliases")
