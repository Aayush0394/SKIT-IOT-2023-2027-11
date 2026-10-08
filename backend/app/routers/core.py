import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Item, Transaction
from .. import schemas
from ..services import inventory, qr
from ..services.event_log import log_event

router = APIRouter(prefix="/api")


# ---------- users ----------
@router.post("/users", response_model=schemas.UserOut, status_code=201)
def create_user(body: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(409, "Email already registered")
    u = User(**body.model_dump())
    db.add(u); db.commit(); db.refresh(u)
    return u


@router.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.id)).all()


# ---------- items ----------
@router.post("/items", response_model=schemas.ItemOut, status_code=201)
def create_item(body: schemas.ItemCreate, db: Session = Depends(get_db)):
    item = Item(**body.model_dump(), quantity_available=body.quantity_total,
                qr_code="ITM-" + uuid.uuid4().hex[:8].upper())
    db.add(item); db.commit(); db.refresh(item)
    log_event("item_created", item_id=item.id)
    return item


@router.get("/items", response_model=list[schemas.ItemOut])
def list_items(db: Session = Depends(get_db)):
    return db.scalars(select(Item).order_by(Item.id)).all()


@router.get("/items/{item_id}/qr.png")
def item_qr(item_id: int, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    return Response(qr.generate_qr_png(item.qr_code), media_type="image/png")


# ---------- scanning / transactions ----------
@router.post("/scan")
def scan_qr(body: schemas.ScanRequest, db: Session = Depends(get_db)):
    return inventory.scan(db, body.qr_payload, body.user_id, body.action)


@router.post("/scan/image")
async def scan_image(user_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        codes = qr.decode_qr_image(await file.read())
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not codes:
        raise HTTPException(422, "No QR code found in image")
    return inventory.scan(db, codes[0], user_id)


@router.get("/transactions", response_model=list[schemas.TransactionOut])
def list_transactions(status: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    q = select(Transaction).order_by(Transaction.id.desc()).limit(limit)
    if status:
        q = q.where(Transaction.status == status)
    return db.scalars(q).all()


@router.get("/status")
def live_status(db: Session = Depends(get_db)):
    """Real-time per-item status: available / issued / returned counts."""
    out = []
    for it in db.scalars(select(Item).order_by(Item.id)):
        returned = sum(1 for t in it.transactions if t.status == "returned")
        out.append({"item_id": it.id, "name": it.name, "available": it.quantity_available,
                    "issued": it.quantity_total - it.quantity_available, "returned_total": returned,
                    "total": it.quantity_total})
    return out
