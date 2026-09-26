"""
app.py
Minimal Flask API for Sprint 3 (QR Generation & Computer Vision
Integration). Exposes item creation + a scan-event endpoint so the
frontend/dashboard team can test the flow without a webcam attached
(e.g. by uploading a QR image, or posting an item_id directly).

Run:
    python app.py
"""

from flask import Flask, jsonify, request
from pyzbar.pyzbar import decode
from PIL import Image

from qr_module.generate_qr import generate_item_qr
from qr_module.models import get_item, init_db, record_scan

app = Flask(__name__)
init_db()


@app.post("/api/items")
def create_item():
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify({"error": "name is required"}), 400
    item = generate_item_qr(name)
    return jsonify(item), 201


@app.get("/api/items/<item_id>")
def item_status(item_id):
    item = get_item(item_id)
    if item is None:
        return jsonify({"error": "item not found"}), 404
    return jsonify(item)


@app.post("/api/scan")
def scan_event():
    """
    Accepts either:
      - JSON: {"item_id": "...", "action": "check_in"|"check_out", "user": "..."}
      - multipart/form-data with an 'image' file containing a QR code
    """
    action = request.values.get("action")
    user = request.values.get("user")
    if action not in ("check_in", "check_out"):
        return jsonify({"error": "action must be check_in or check_out"}), 400

    if "image" in request.files:
        img = Image.open(request.files["image"].stream)
        results = decode(img)
        if not results:
            return jsonify({"error": "no QR code detected in image"}), 400
        item_id = results[0].data.decode("utf-8")
    else:
        data = request.get_json(silent=True) or {}
        item_id = data.get("item_id") or request.values.get("item_id")

    if not item_id:
        return jsonify({"error": "item_id is required"}), 400

    item = get_item(item_id)
    if item is None:
        return jsonify({"error": f"unknown item_id {item_id}"}), 404

    updated = record_scan(item_id, action, user)
    return jsonify(updated)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
