from decimal import Decimal

from pydantic import BaseModel


class ClaimComparisonItem(BaseModel):
    claim_id: int
    creditor: str | None
    amount: Decimal | None
    currency: str
    claim_reference: str | None
    contract_reference: str | None
    status: str


class ClaimComparisonGroup(BaseModel):
    reason: str
    items: list[ClaimComparisonItem]
