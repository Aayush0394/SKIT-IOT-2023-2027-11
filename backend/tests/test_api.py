import os
import tempfile

_db = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db}"

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def test_full_flow():
    with TestClient(app) as c:
        u = c.post("/api/users", json={"name": "T", "email": "t@x.com"}).json()
        it = c.post("/api/items", json={"name": "Sensor", "quantity_total": 2}).json()
        r = c.post("/api/scan", json={"qr_payload": f"INV:{it['qr_code']}", "user_id": u["id"]}).json()
        assert r["action"] == "issue"
        assert c.get("/api/status").json()[0]["issued"] == 1
        r = c.post("/api/scan", json={"qr_payload": it["qr_code"], "user_id": u["id"]}).json()
        assert r["action"] == "return"
        assert c.get("/api/status").json()[0]["available"] == 2
        assert c.get("/api/analytics/forecast").status_code == 200
        assert c.get(f"/api/items/{it['id']}/qr.png").headers["content-type"] == "image/png"
        assert c.post("/api/scan", json={"qr_payload": "INV:NOPE", "user_id": u["id"]}).status_code == 404
