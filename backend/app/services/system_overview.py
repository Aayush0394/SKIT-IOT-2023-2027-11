"""Read-only system overview for the inventory admin dashboard."""
from sqlalchemy.orm import Session
from ..models import Item, User, Transaction
from .health_checks import database_summary, operational_metrics
from .health_checks import inventory_integrity, transaction_integrity


def inventory_totals(db: Session) -> dict:
    items = db.query(Item).all()
    total = sum(max(0, row.quantity_total) for row in items)
    available = sum(max(0, row.quantity_available) for row in items)
    return {
        "item_types": len(items), "total_units": total,
        "available_units": available, "occupied_units": max(0, total-available),
        "availability_percent": round(available * 100 / total, 2) if total else 0.0,
    }


def user_totals(db: Session) -> dict:
    users = db.query(User).all()
    roles = {}
    for user in users:
        role = (user.role or "member").lower()
        roles[role] = roles.get(role, 0) + 1
    return {"total_users": len(users), "by_role": roles}


def transaction_totals(db: Session) -> dict:
    rows = db.query(Transaction).all()
    issued = sum(row.status == "issued" for row in rows)
    returned = sum(row.status == "returned" for row in rows)
    return {
        "total_transactions": len(rows), "issued": issued,
        "returned": returned, "unknown_status": len(rows)-issued-returned,
    }


def build_system_overview(db: Session) -> dict:
    inventory_errors = inventory_integrity(db)
    transaction_errors = transaction_integrity(db)
    errors = inventory_errors + transaction_errors
    return {
        "system_status": "healthy" if not errors else "attention_required",
        "database": database_summary(db),
        "inventory": inventory_totals(db),
        "users": user_totals(db),
        "transactions": transaction_totals(db),
        "operations": operational_metrics(db),
        "integrity": {
            "total_errors": len(errors),
            "inventory_errors": inventory_errors,
            "transaction_errors": transaction_errors,
        },
    }


def readiness_message(report: dict) -> str:
    if report.get("system_status") == "healthy":
        return "Inventory system checks completed successfully."
    count = report.get("integrity", {}).get("total_errors", 0)
    return f"Attention required: {count} data integrity issue(s) found."
