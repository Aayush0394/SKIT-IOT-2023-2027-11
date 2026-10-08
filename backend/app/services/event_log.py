"""Event logging for analytics. MongoDB if MONGO_URI set, else JSONL file."""
import json
from datetime import datetime, timezone
from pathlib import Path

from ..config import settings

_LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
_mongo = None


def _get_mongo():
    global _mongo
    if _mongo is None and settings.MONGO_URI:
        try:
            from pymongo import MongoClient
            client = MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=2000)
            _mongo = client[settings.MONGO_DB]
            _mongo.events.create_index([("ts", -1)])
            _mongo.events.create_index("type")
        except Exception:
            _mongo = None
    return _mongo


def log_event(event_type: str, **data) -> None:
    doc = {"type": event_type, "ts": datetime.now(timezone.utc).isoformat(), **data}
    db = _get_mongo()
    if db is not None:
        try:
            db.events.insert_one(dict(doc))
            return
        except Exception:
            pass
    _LOG_DIR.mkdir(exist_ok=True)
    with open(_LOG_DIR / "events.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(doc, default=str) + "\n")
