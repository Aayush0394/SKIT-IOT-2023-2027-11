"""Filtered and paginated transaction reporting endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.transaction_reports import (
    list_transaction_rows, count_transactions, transaction_summary,
    serialize_transaction,
)

router = APIRouter(prefix="/api/reports/transactions", tags=["transaction-reports"])


@router.get("")
def search_transactions(
    status: str | None = Query(None),
    user_id: int | None = Query(None, ge=1),
    item_id: int | None = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search transactions with filters and safe pagination."""
    try:
        rows = list_transaction_rows(db, status, user_id, item_id, offset, limit)
        total = count_transactions(db, status, user_id, item_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(rows) < total,
        "transactions": [serialize_transaction(row) for row in rows],
    }


@router.get("/summary")
def transaction_activity_summary(
    days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)
):
    """Return issue, return and overdue counts for a recent period."""
    return transaction_summary(db, days)
