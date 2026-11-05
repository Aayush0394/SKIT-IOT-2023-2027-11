"""Popularity clustering endpoint for dashboard and ML evaluation."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..ml.popularity_analysis import popularity_report

router = APIRouter(prefix="/api/analytics", tags=["popularity-analysis"])


@router.get("/popularity-clusters")
def get_popularity_clusters(
    days: int = Query(30, ge=1, le=365),
    clusters: int = Query(3, ge=1, le=8),
    db: Session = Depends(get_db),
):
    """Return item activity groups for the requested analysis window."""
    return popularity_report(db, days, clusters)
