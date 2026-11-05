"""Read-only system diagnostics for the inventory application."""
from datetime import timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from ..models import Item, User, Transaction, utcnow


def database_summary(db: Session) -> dict:
    """Return basic table counts without loading every row into memory."""
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "items": db.scalar(select(func.count()).select_from(Item)) or 0,
        "transactions": db.scalar(select(func.count()).select_from(Transaction)) or 0,
    }


def inventory_integrity(db: Session) -> list[dict]:
    """Find item quantity values that violate inventory invariants."""
    problems = []
    items = db.scalars(select(Item).order_by(Item.id)).all()
    for item in items:
        if item.quantity_total < 0:
            problems.append({"item_id": item.id, "issue": "negative_total"})
        if item.quantity_available < 0:
            problems.append({"item_id": item.id, "issue": "negative_available"})
        if item.quantity_available > item.quantity_total:
            problems.append({"item_id": item.id, "issue": "available_exceeds_total"})
        if not item.qr_code:
            problems.append({"item_id": item.id, "issue": "missing_qr_code"})
    return problems


def transaction_integrity(db: Session) -> list[dict]:
    """Check transaction dates and references for obvious data problems."""
    problems = []
    rows = db.scalars(select(Transaction).order_by(Transaction.id)).all()
    for tx in rows:
        if tx.due_at < tx.issued_at:
            problems.append({"transaction_id": tx.id, "issue": "due_before_issue"})
        if tx.returned_at and tx.returned_at < tx.issued_at:
            problems.append({"transaction_id": tx.id, "issue": "return_before_issue"})
        if tx.status == "returned" and tx.returned_at is None:
            problems.append({"transaction_id": tx.id, "issue": "returned_without_timestamp"})
        if tx.status == "issued" and tx.returned_at is not None:
            problems.append({"transaction_id": tx.id, "issue": "issued_with_return_timestamp"})
    return problems


def operational_metrics(db: Session) -> dict:
    """Produce a small operational snapshot for the team lead."""
    now = utcnow()
    week_ago = now - timedelta(days=7)
    active = db.scalars(select(Transaction).where(Transaction.status == "issued")).all()
    recent = db.scalar(select(func.count()).select_from(Transaction).where(
        Transaction.issued_at >= week_ago
    )) or 0
    overdue = sum(1 for tx in active if tx.due_at < now)
    return {
        "active_transactions": len(active),
        "overdue_transactions": overdue,
        "issues_last_7_days": recent,
        "generated_at": now.isoformat(),
    }


def build_diagnostic_report(db: Session) -> dict:
    """Combine read-only checks; this function never modifies project data."""
    inventory_errors = inventory_integrity(db)
    transaction_errors = transaction_integrity(db)
    errors = inventory_errors + transaction_errors
    return {
        "status": "healthy" if not errors else "attention_required",
        "database": database_summary(db),
        "operations": operational_metrics(db),
        "integrity": {
            "error_count": len(errors),
            "inventory_errors": inventory_errors,
            "transaction_errors": transaction_errors,
        },
    }
