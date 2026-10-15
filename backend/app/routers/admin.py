"""Admin-oriented reports for overdue inventory loans. Demo fee calculation only."""
from datetime import timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Transaction, User, Item, utcnow

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/overdue")
def overdue_transactions(daily_fee: float = Query(5.0, ge=0, le=10000), db: Session = Depends(get_db)):
    """List unreturned transactions past due and estimate fee (not a payment record)."""
    now = utcnow()
    rows = db.scalars(select(Transaction).where(Transaction.status == "issued", Transaction.due_at < now).order_by(Transaction.due_at)).all()
    result=[]
    for tx in rows:
        days_late=max(0, (now.date()-tx.due_at.date()).days)
        result.append({"transaction_id":tx.id,"item_id":tx.item_id,"item_name":tx.item.name,
          "user_id":tx.user_id,"user_name":tx.user.name,"due_at":tx.due_at,
          "days_overdue":days_late,"estimated_fee":round(days_late*daily_fee,2)})
    return {"daily_fee":daily_fee,"count":len(result),"estimated_total":round(sum(r['estimated_fee'] for r in result),2),"transactions":result}

@router.get("/summary")
def admin_summary(db: Session = Depends(get_db)):
    users=db.scalars(select(User)).all(); items=db.scalars(select(Item)).all(); txs=db.scalars(select(Transaction)).all()
    return {"users":len(users),"items":len(items),"total_units":sum(i.quantity_total for i in items),
      "available_units":sum(i.quantity_available for i in items),"active_loans":sum(t.status=="issued" for t in txs),
      "returned_loans":sum(t.status=="returned" for t in txs)}
