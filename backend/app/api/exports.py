import csv
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.models.creditor import Creditor

router = APIRouter()


@router.get("/claims.csv")
def export_claims_csv(db: Session = Depends(get_db)) -> StreamingResponse:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "claim_id",
            "creditor",
            "amount",
            "currency",
            "claim_reference",
            "contract_reference",
            "title_exists",
            "title_type",
            "status",
            "first_seen",
            "last_seen",
        ]
    )
    rows = db.execute(select(Claim, Creditor).outerjoin(Creditor, Claim.creditor_id == Creditor.id)).all()
    for claim, creditor in rows:
        writer.writerow(
            [
                claim.id,
                creditor.canonical_name if creditor else "",
                claim.amount or "",
                claim.currency,
                claim.claim_reference or "",
                claim.contract_reference or "",
                claim.title_exists,
                claim.title_type or "",
                claim.status,
                claim.first_seen or "",
                claim.last_seen or "",
            ]
        )
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="debtai-claims.csv"'},
    )
