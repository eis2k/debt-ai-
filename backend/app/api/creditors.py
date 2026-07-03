from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.claim import Claim
from app.models.creditor import Creditor
from app.schemas.creditor import CreditorDetail, CreditorSummary

router = APIRouter()


@router.get("", response_model=list[CreditorSummary])
def list_creditors(db: Session = Depends(get_db)) -> list[CreditorSummary]:
    rows = db.execute(
        select(
            Creditor.id,
            Creditor.canonical_name,
            Creditor.active,
            func.count(Claim.id).label("claim_count"),
            func.coalesce(func.sum(Claim.amount), 0).label("total_amount"),
            func.coalesce(
                func.sum(case((Claim.status != "paid", Claim.amount), else_=0)),
                0,
            ).label("open_amount"),
        )
        .outerjoin(Claim, Claim.creditor_id == Creditor.id)
        .group_by(Creditor.id)
        .order_by(Creditor.canonical_name)
    ).all()
    return [
        CreditorSummary(
            id=row.id,
            canonical_name=row.canonical_name,
            active=row.active,
            claim_count=row.claim_count,
            total_amount=Decimal(row.total_amount or 0),
            open_amount=Decimal(row.open_amount or 0),
        )
        for row in rows
    ]


@router.get("/{creditor_id}", response_model=CreditorDetail)
def get_creditor(creditor_id: int, db: Session = Depends(get_db)) -> CreditorDetail:
    creditor = db.scalar(
        select(Creditor)
        .where(Creditor.id == creditor_id)
        .options(selectinload(Creditor.aliases), selectinload(Creditor.claims))
    )
    if creditor is None:
        raise HTTPException(status_code=404, detail="Creditor not found")
    return CreditorDetail(
        id=creditor.id,
        canonical_name=creditor.canonical_name,
        active=creditor.active,
        notes=creditor.notes,
        aliases=[alias.alias for alias in creditor.aliases],
        claims=creditor.claims,
    )
