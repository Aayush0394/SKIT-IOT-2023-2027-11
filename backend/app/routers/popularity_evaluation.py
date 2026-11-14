"""Popularity clustering evaluation endpoint."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..ml.popularity_analysis import collect_item_activity
from ..ml.popularity_evaluation import (
    evaluate_popularity_rows, popularity_quality_label,
)

router = APIRouter(prefix="/api/analytics", tags=["popularity-evaluation"])


@router.get("/popularity-evaluation")
def evaluate_popularity(
    days: int = Query(30, ge=1, le=365),
    clusters: int = Query(3, ge=1, le=8),
    db: Session = Depends(get_db),
):
    rows = collect_item_activity(db, days)
    report = evaluate_popularity_rows(rows, clusters)
    report["period_days"] = days
    report["algorithm"] = "kmeans_frequency_analysis"
    report["quality_label"] = popularity_quality_label(report)
    return report
