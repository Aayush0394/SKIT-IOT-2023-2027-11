"""
models.py
Lightweight SQLite layer for inventory items and scan events.
Swap this out for MySQL/PostgreSQL (per FR/NFR docs) once the team's
main backend schema (Sprint 2) is ready -- the function signatures
below are written so that swap only touches this file.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = "inventory.db"


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                item_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'available',  -- available | issued | returned
                issued_to TEXT,
                issued_at TEXT,
                due_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scan_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                action TEXT NOT NULL,       -- check_in | check_out
                scanned_at TEXT NOT NULL,
                FOREIGN KEY (item_id) REFERENCES items (item_id)
            )
        """)


def add_item(item_id: str, name: str):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO items (item_id, name) VALUES (?, ?)",
            (item_id, name),
        )


def get_item(item_id: str):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM items WHERE item_id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None


def record_scan(item_id: str, action: str, user: str | None = None):
    """
    action: 'check_out' (issue) or 'check_in' (return)
    Updates item status + logs the scan event. Returns the updated item.
    """
    now = datetime.utcnow().isoformat()
    with get_conn() as conn:
        if action == "check_out":
            conn.execute(
                """UPDATE items SET status='issued', issued_to=?, issued_at=?
                   WHERE item_id=?""",
                (user, now, item_id),
            )
        elif action == "check_in":
            conn.execute(
                """UPDATE items SET status='available', issued_to=NULL,
                   issued_at=NULL WHERE item_id=?""",
                (item_id,),
            )
        else:
            raise ValueError("action must be 'check_out' or 'check_in'")

        conn.execute(
            "INSERT INTO scan_events (item_id, action, scanned_at) VALUES (?, ?, ?)",
            (item_id, action, now),
        )
        row = conn.execute(
            "SELECT * FROM items WHERE item_id = ?", (item_id,)
        ).fetchone()
        return dict(row) if row else None
