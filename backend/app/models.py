"""Relational schema: users, items, transactions."""
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    # naive UTC keeps SQLite / MySQL / PostgreSQL behaviour identical
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(20), default="member")  # member | admin
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    transactions = relationship("Transaction", back_populates="user")


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(80), default="General")
    qr_code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    quantity_total: Mapped[int] = mapped_column(Integer, default=1)
    quantity_available: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    transactions = relationship("Transaction", back_populates="item")


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    due_at: Mapped[datetime] = mapped_column(DateTime)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="issued")  # issued | returned
    item = relationship("Item", back_populates="transactions")
    user = relationship("User", back_populates="transactions")
