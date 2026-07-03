from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.models.creditor import Creditor
from app.models.document import Document
from app.schemas.dashboard import DashboardStatusBucket, DashboardSummary

router = APIRouter()


@router.get("", response_model=DashboardSummary)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardSummary:
    document_count = db.scalar(select(func.count(Document.id))) or 0
    creditor_count = db.scalar(select(func.count(Creditor.id))) or 0
    claim_count = db.scalar(select(func.count(Claim.id))) or 0
    total_claim_amount = db.scalar(select(func.coalesce(func.sum(Claim.amount), 0))) or 0
    open_claim_amount = (
        db.scalar(select(func.coalesce(func.sum(Claim.amount), 0)).where(Claim.status != "paid")) or 0
    )
    titled_claim_count = db.scalar(select(func.count(Claim.id)).where(Claim.title_exists.is_(True))) or 0
    rows = db.execute(
        select(
            Claim.status,
            func.count(Claim.id).label("count"),
            func.coalesce(func.sum(Claim.amount), 0).label("amount"),
        )
        .group_by(Claim.status)
        .order_by(Claim.status)
    ).all()
    return DashboardSummary(
        document_count=document_count,
        creditor_count=creditor_count,
        claim_count=claim_count,
        total_claim_amount=Decimal(total_claim_amount or 0),
        open_claim_amount=Decimal(open_claim_amount or 0),
        titled_claim_count=titled_claim_count,
        status_buckets=[
            DashboardStatusBucket(status=row.status, count=row.count, amount=Decimal(row.amount or 0)) for row in rows
        ],
    )
