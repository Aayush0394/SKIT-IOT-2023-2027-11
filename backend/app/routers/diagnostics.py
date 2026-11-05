"""Team-lead endpoints for application health and data integrity."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.health_checks import build_diagnostic_report

router = APIRouter(prefix="/api/admin/diagnostics", tags=["admin-diagnostics"])


@router.get("/summary")
def diagnostic_summary(db: Session = Depends(get_db)):
    """Return counts, operational metrics and integrity warnings."""
    return build_diagnostic_report(db)


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """Simple readiness response suitable for a dashboard status indicator."""
    report = build_diagnostic_report(db)
    ready = report["status"] == "healthy"
    return {
        "ready": ready,
        "status": report["status"],
        "integrity_error_count": report["integrity"]["error_count"],
    }
