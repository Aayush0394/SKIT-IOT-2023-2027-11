"""QR generation + decoding (OpenCV + pyzbar)."""
import io

import numpy as np

PREFIX = "INV:"


def make_payload(qr_code: str) -> str:
    return f"{PREFIX}{qr_code}"


def parse_payload(payload: str) -> str:
    payload = payload.strip()
    return payload[len(PREFIX):] if payload.startswith(PREFIX) else payload


def generate_qr_png(qr_code: str) -> bytes:
    import qrcode
    img = qrcode.make(make_payload(qr_code))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def decode_qr_image(image_bytes: bytes) -> list[str]:
    """Decode every QR in an image. Uses pyzbar, falls back to OpenCV's detector."""
    import cv2
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    results: list[str] = []
    try:
        from pyzbar.pyzbar import decode
        results = [d.data.decode("utf-8") for d in decode(img)]
    except Exception:  # pyzbar / libzbar missing
        results = []
    if not results:
        data, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
        if data:
            results = [data]
    return results
