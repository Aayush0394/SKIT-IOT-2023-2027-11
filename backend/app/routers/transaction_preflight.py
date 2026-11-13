"""Preflight endpoints for proposed inventory transactions."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.transaction_preflight import (
    validate_transaction_request, validate_batch_requests,
)

router = APIRouter(prefix="/api/transactions", tags=["transaction-preflight"])


class PreflightRequest(BaseModel):
    item_id: int = Field(gt=0)
    user_id: int = Field(gt=0)
    action: str


class BatchPreflightRequest(BaseModel):
    requests: list[PreflightRequest] = Field(min_length=1, max_length=50)


@router.post("/preflight")
def transaction_preflight(payload: PreflightRequest, db: Session = Depends(get_db)):
    result = validate_transaction_request(
        db, payload.item_id, payload.user_id, payload.action
    )
    if result["action"] not in {"issue", "return"}:
        raise HTTPException(status_code=422, detail=result["errors"])
    return result


@router.post("/preflight/batch")
def batch_transaction_preflight(
    payload: BatchPreflightRequest, db: Session = Depends(get_db)
):
    requests = [row.model_dump() for row in payload.requests]
    return validate_batch_requests(db, requests)
