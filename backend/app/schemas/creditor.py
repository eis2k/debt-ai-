from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class ClaimRead(BaseModel):
    id: int
    amount: Decimal | None
    currency: str
    claim_reference: str | None
    contract_reference: str | None
    title_exists: bool
    title_type: str | None
    status: str
    first_seen: date | None
    last_seen: date | None

    model_config = ConfigDict(from_attributes=True)


class CreditorSummary(BaseModel):
    id: int
    canonical_name: str
    active: bool
    claim_count: int
    total_amount: Decimal
    open_amount: Decimal


class CreditorDetail(BaseModel):
    id: int
    canonical_name: str
    active: bool
    notes: str | None
    aliases: list[str]
    claims: list[ClaimRead]

    model_config = ConfigDict(from_attributes=True)
