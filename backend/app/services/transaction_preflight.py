"""Read-only validation before issue/return operations."""
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..models import Item, User, Transaction

VALID_ACTIONS = {"issue", "return"}


def validate_transaction_request(db: Session, item_id: int, user_id: int, action: str) -> dict:
    problems = []
    action = (action or "").strip().lower()
    if action not in VALID_ACTIONS:
        return {"valid": False, "action": action,
                "errors": ["Action must be 'issue' or 'return'."]}
    item = db.get(Item, item_id)
    user = db.get(User, user_id)
    if item is None:
        problems.append("Item does not exist.")
    if user is None:
        problems.append("User does not exist.")
    if item is None or user is None:
        return {"valid": False, "action": action, "errors": problems}

    active = db.scalar(select(Transaction).where(
        Transaction.item_id == item.id,
        Transaction.user_id == user.id,
        Transaction.status == "issued",
    ))
    if action == "issue":
        if item.quantity_available < 1:
            problems.append("Item is currently out of stock.")
        if active is not None:
            problems.append("User already has an active issue for this item.")
    elif active is None:
        problems.append("No active issue exists for this user and item.")

    return {
        "valid": not problems, "action": action,
        "item": {"id": item.id, "name": item.name,
                 "available": item.quantity_available, "total": item.quantity_total},
        "user": {"id": user.id, "name": user.name},
        "active_transaction_id": active.id if active is not None else None,
        "errors": problems,
        "note": "Preflight only; no database values were changed.",
    }


def validate_batch_requests(db: Session, requests: list[dict]) -> dict:
    results = []
    for number, request in enumerate(requests, start=1):
        result = validate_transaction_request(
            db, int(request.get("item_id", 0)),
            int(request.get("user_id", 0)), str(request.get("action", "")),
        )
        result["request_number"] = number
        results.append(result)
    valid_count = sum(1 for result in results if result["valid"])
    return {"total": len(results), "valid": valid_count,
            "invalid": len(results)-valid_count, "results": results}
