"""Core check-in / check-out logic (QR scan flow)."""
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Item, User, Transaction, utcnow
from .qr import parse_payload
from .event_log import log_event


def scan(db: Session, qr_payload: str, user_id: int, action: str | None = None) -> dict:
    code = parse_payload(qr_payload)
    item = db.scalar(select(Item).where(Item.qr_code == code))
    if not item:
        raise HTTPException(404, f"No item for QR '{code}'")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    open_tx = db.scalar(select(Transaction).where(
        Transaction.item_id == item.id, Transaction.user_id == user.id, Transaction.status == "issued"))
    action = action or ("return" if open_tx else "issue")

    if action == "issue":
        if item.quantity_available < 1:
            raise HTTPException(409, f"'{item.name}' is out of stock")
        now = utcnow()
        tx = Transaction(item_id=item.id, user_id=user.id, issued_at=now,
                         due_at=now + timedelta(days=settings.LOAN_DAYS), status="issued")
        item.quantity_available -= 1
        db.add(tx)
        db.flush()
        log_event("issue", item_id=item.id, user_id=user.id, txn_id=tx.id)
        db.commit()
        return {"action": "issue", "message": f"Issued '{item.name}' to {user.name}. Due {tx.due_at:%d %b %Y}.",
                "transaction_id": tx.id}

    if action == "return":
        if not open_tx:
            raise HTTPException(409, "No open issue of this item for this user")
        open_tx.returned_at, open_tx.status = utcnow(), "returned"
        item.quantity_available = min(item.quantity_total, item.quantity_available + 1)
        log_event("return", item_id=item.id, user_id=user.id, txn_id=open_tx.id)
        db.commit()
        return {"action": "return", "message": f"Returned '{item.name}'.", "transaction_id": open_tx.id}

    raise HTTPException(400, "action must be 'issue' or 'return'")


def daily_issue_counts(db: Session, item_id: int | None = None, days: int = 30) -> list[int]:
    """Issues per day for the last `days` days, oldest -> newest (zeros included)."""
    start = (utcnow() - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    q = select(Transaction.issued_at).where(Transaction.issued_at >= start)
    if item_id:
        q = q.where(Transaction.item_id == item_id)
    counts = [0] * days
    for (ts,) in db.execute(q):
        counts[min(days - 1, max(0, (ts - start).days))] += 1
    return counts
