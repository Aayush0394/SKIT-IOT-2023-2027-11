"""Team lead system overview API."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.system_overview import build_system_overview, readiness_message

router = APIRouter(prefix="/api/admin", tags=["admin-overview"])


@router.get("/system-overview")
def system_overview(db: Session = Depends(get_db)):
    report = build_system_overview(db)
    report["message"] = readiness_message(report)
    return report


@router.get("/system-overview/readiness")
def system_readiness(db: Session = Depends(get_db)):
    report = build_system_overview(db)
    return {
        "ready": report["system_status"] == "healthy",
        "status": report["system_status"],
        "integrity_error_count": report["integrity"]["total_errors"],
        "message": readiness_message(report),
    }
