from datetime import date, datetime

from pydantic import BaseModel


class ClaimTransferRead(BaseModel):
    id: int
    claim_id: int
    claim_reference: str | None
    contract_reference: str | None
    from_creditor_id: int | None
    from_creditor_name: str | None
    to_creditor_id: int | None
    to_creditor_name: str | None
    document_id: int | None
    document_filename: str | None
    transfer_date: date | None
    notes: str | None
    created_at: datetime
