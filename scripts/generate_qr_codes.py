"""Generate printable QR PNGs for every item:  python scripts/generate_qr_codes.py (from repo root)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.database import SessionLocal  # noqa: E402
from app.models import Item  # noqa: E402
from app.services.qr import generate_qr_png  # noqa: E402

out = Path("qr_codes")
out.mkdir(exist_ok=True)
with SessionLocal() as db:
    for it in db.query(Item):
        (out / f"{it.qr_code}_{it.name.replace(' ', '_')}.png").write_bytes(generate_qr_png(it.qr_code))
        print("wrote", it.qr_code, it.name)
