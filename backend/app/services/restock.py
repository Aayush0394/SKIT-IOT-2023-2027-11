"""Explainable low-stock/reorder recommendations; does not place purchase orders."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Item
from .inventory import daily_issue_counts
from ..ml.demand import forecast_demand

def build_restock_suggestions(db: Session, threshold: int = 2, horizon: int = 7) -> list[dict]:
    suggestions=[]
    for item in db.scalars(select(Item).order_by(Item.id)).all():
        if item.quantity_available > threshold:
            continue
        history=daily_issue_counts(db, item.id, 30)
        forecast=forecast_demand(history, horizon)
        projected=max(0, int(round(forecast["total"])))
        target=max(threshold+1, projected)
        needed=max(0, target-item.quantity_available)
        suggestions.append({"item_id":item.id,"name":item.name,"category":item.category,
          "quantity_available":item.quantity_available,"threshold":threshold,
          "forecast_next_days":horizon,"predicted_demand":forecast["total"],
          "suggested_reorder_quantity":needed,"reason":"at/below configured stock threshold"})
    return suggestions
