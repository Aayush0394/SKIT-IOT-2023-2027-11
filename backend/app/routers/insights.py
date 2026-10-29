"""Popularity and dashboard KPI endpoints based on recorded transactions."""
from datetime import timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Item, Transaction, User, utcnow
router=APIRouter(prefix="/api/insights", tags=["insights"])

@router.get("/popular-items")
def popular_items(days:int=Query(30,ge=1,le=365), limit:int=Query(10,ge=1,le=100), db:Session=Depends(get_db)):
    cutoff=utcnow()-timedelta(days=days)
    items=db.scalars(select(Item).order_by(Item.id)).all()
    counts={i.id:0 for i in items}
    for tx in db.scalars(select(Transaction).where(Transaction.issued_at>=cutoff)):
        counts[tx.item_id]=counts.get(tx.item_id,0)+1
    ranked=sorted(items,key=lambda i:(counts.get(i.id,0),i.name.lower()),reverse=True)[:limit]
    return {"period_days":days,"items":[{"item_id":i.id,"name":i.name,"category":i.category,"issue_count":counts.get(i.id,0),"available":i.quantity_available} for i in ranked]}

@router.get("/dashboard")
def dashboard(db:Session=Depends(get_db)):
    users=db.scalars(select(User)).all(); items=db.scalars(select(Item)).all(); txs=db.scalars(select(Transaction)).all()
    now=utcnow(); recent=now-timedelta(days=7)
    return {"users_total":len(users),"items_total":len(items),"units_total":sum(i.quantity_total for i in items),
      "units_available":sum(i.quantity_available for i in items),"active_loans":sum(t.status=="issued" for t in txs),
      "overdue_loans":sum(t.status=="issued" and t.due_at<now for t in txs),
      "issues_last_7_days":sum(t.issued_at>=recent for t in txs),
      "returns_total":sum(t.status=="returned" for t in txs)}
