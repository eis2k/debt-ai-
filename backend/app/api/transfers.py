from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.db.session import get_db
from app.models.claim import Claim, ClaimTransfer
from app.models.creditor import Creditor
from app.models.document import Document
from app.schemas.transfer import ClaimTransferRead

router = APIRouter()


@router.get("", response_model=list[ClaimTransferRead])
def list_transfers(db: Session = Depends(get_db)) -> list[ClaimTransferRead]:
    from_creditor = aliased(Creditor)
    to_creditor = aliased(Creditor)
    rows = db.execute(
        select(ClaimTransfer, Claim, from_creditor, to_creditor, Document)
        .join(Claim, Claim.id == ClaimTransfer.claim_id)
        .outerjoin(from_creditor, from_creditor.id == ClaimTransfer.from_creditor_id)
        .outerjoin(to_creditor, to_creditor.id == ClaimTransfer.to_creditor_id)
        .outerjoin(Document, Document.id == ClaimTransfer.document_id)
        .order_by(ClaimTransfer.transfer_date.desc().nullslast(), ClaimTransfer.created_at.desc())
    ).all()

    return [
        ClaimTransferRead(
            id=transfer.id,
            claim_id=claim.id,
            claim_reference=claim.claim_reference,
            contract_reference=claim.contract_reference,
            from_creditor_id=old.id if old else None,
            from_creditor_name=old.canonical_name if old else None,
            to_creditor_id=new.id if new else None,
            to_creditor_name=new.canonical_name if new else None,
            document_id=document.id if document else None,
            document_filename=document.filename if document else None,
            transfer_date=transfer.transfer_date,
            notes=transfer.notes,
            created_at=transfer.created_at,
        )
        for transfer, claim, old, new, document in rows
    ]
