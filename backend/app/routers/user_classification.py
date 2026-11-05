"""API endpoints for classifying inventory users by borrowing behaviour."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..ml.user_classification import classify_user

router = APIRouter(prefix="/api/users", tags=["user-classification"])


@router.get("/{user_id}/classification")
def get_user_classification(
    user_id: int,
    days: int = Query(180, ge=1, le=730),
    db: Session = Depends(get_db),
):
    """Return Premium/Regular/Risky class and the behaviour features."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    result = classify_user(db, user_id, days)
    return {"user_id": user.id, "user_name": user.name, **result}
