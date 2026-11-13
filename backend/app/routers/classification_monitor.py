"""Batch classification report and review API."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.classification_monitor import build_classification_monitor

router = APIRouter(prefix="/api/users", tags=["classification-monitor"])


@router.get("/classification-report")
def classification_report(
    days: int = Query(180, ge=1, le=730),
    db: Session = Depends(get_db),
):
    return build_classification_monitor(db, days)


@router.get("/classification-review")
def classification_review(
    days: int = Query(180, ge=1, le=730),
    db: Session = Depends(get_db),
):
    report = build_classification_monitor(db, days)
    return {
        "period_days": days,
        "review_count": report["manual_review_count"],
        "users": report["manual_review"],
        "notice": report["model_notice"],
    }
