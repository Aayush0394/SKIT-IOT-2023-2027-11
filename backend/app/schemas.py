from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    name: str
    email: str
    role: str = "member"


class UserOut(ORM):
    id: int
    name: str
    email: str
    role: str


class ItemCreate(BaseModel):
    name: str
    category: str = "General"
    quantity_total: int = 1


class ItemOut(ORM):
    id: int
    name: str
    category: str
    qr_code: str
    quantity_total: int
    quantity_available: int


class TransactionOut(ORM):
    id: int
    item_id: int
    user_id: int
    issued_at: datetime
    due_at: datetime
    returned_at: datetime | None
    status: str


class ScanRequest(BaseModel):
    qr_payload: str
    user_id: int
    action: str | None = None  # "issue" | "return" | None = auto-toggle
