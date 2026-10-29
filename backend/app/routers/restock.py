from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.restock import build_restock_suggestions
router=APIRouter(prefix="/api/restock", tags=["restock"])

@router.get("/suggestions")
def restock_suggestions(threshold:int=Query(2,ge=0,le=100000), horizon:int=Query(7,ge=1,le=90), db:Session=Depends(get_db)):
    rows=build_restock_suggestions(db, threshold, horizon)
    return {"count":len(rows),"suggestions":rows,"automatic_purchase_enabled":False}
