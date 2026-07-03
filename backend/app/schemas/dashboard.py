from decimal import Decimal

from pydantic import BaseModel


class DashboardStatusBucket(BaseModel):
    status: str
    count: int
    amount: Decimal


class DashboardSummary(BaseModel):
    document_count: int
    creditor_count: int
    claim_count: int
    total_claim_amount: Decimal
    open_claim_amount: Decimal
    titled_claim_count: int
    status_buckets: list[DashboardStatusBucket]
