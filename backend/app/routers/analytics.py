from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.inventory import daily_issue_counts
from ..ml import demand

router = APIRouter(prefix="/api/analytics")


@router.get("/forecast")
def forecast(item_id: int | None = None, horizon: int = 7, db: Session = Depends(get_db)):
    """Baseline stock demand prediction (linear regression on daily issue counts)."""
    hist = daily_issue_counts(db, item_id, 30)
    return {"history": hist, **demand.forecast_demand(hist, horizon)}
