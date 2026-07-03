from collections import defaultdict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.claim import Claim
from app.models.creditor import Creditor
from app.schemas.comparison import ClaimComparisonGroup, ClaimComparisonItem

router = APIRouter()


@router.get("/claims", response_model=list[ClaimComparisonGroup])
def compare_claims(db: Session = Depends(get_db)) -> list[ClaimComparisonGroup]:
    rows = db.execute(select(Claim, Creditor).outerjoin(Creditor, Claim.creditor_id == Creditor.id)).all()
    groups: dict[tuple[str, str], list[ClaimComparisonItem]] = defaultdict(list)
    for claim, creditor in rows:
        item = ClaimComparisonItem(
            claim_id=claim.id,
            creditor=creditor.canonical_name if creditor else None,
            amount=claim.amount,
            currency=claim.currency,
            claim_reference=claim.claim_reference,
            contract_reference=claim.contract_reference,
            status=claim.status,
        )
        if claim.claim_reference:
            groups[("Gleiches Aktenzeichen", claim.claim_reference)].append(item)
        if creditor and claim.amount is not None:
            groups[(f"Gleicher Glaeubiger und Betrag ({creditor.canonical_name})", str(claim.amount))].append(item)

    return [
        ClaimComparisonGroup(reason=reason, items=items)
        for (reason, _), items in groups.items()
        if len(items) > 1
    ]
