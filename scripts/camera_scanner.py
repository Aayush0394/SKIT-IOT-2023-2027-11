"""Live webcam QR scanner (OpenCV + pyzbar) -> calls the backend /api/scan.

Usage:  python scripts/camera_scanner.py --user 2 [--api http://localhost:8000]
Press q to quit. The same QR twice in a row within 4s is ignored (debounce).
"""
import argparse
import time

import cv2
import requests

try:
    from pyzbar.pyzbar import decode as zbar_decode
except Exception:  # libzbar missing -> OpenCV fallback
    zbar_decode = None


def read_codes(frame, detector):
    if zbar_decode:
        codes = [d.data.decode() for d in zbar_decode(frame)]
        if codes:
            return codes
    data, _, _ = detector.detectAndDecode(frame)
    return [data] if data else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--user", type=int, required=True)
    ap.add_argument("--api", default="http://localhost:8000")
    ap.add_argument("--camera", type=int, default=0)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.camera)
    det = cv2.QRCodeDetector()
    last, last_t, msg = None, 0.0, "Show a QR code..."
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        for code in read_codes(frame, det):
            if code == last and time.time() - last_t < 4:
                continue
            last, last_t = code, time.time()
            try:
                r = requests.post(f"{a.api}/api/scan", json={"qr_payload": code, "user_id": a.user}, timeout=5)
                msg = r.json().get("message") or r.json().get("detail", "error")
            except Exception as e:
                msg = f"API error: {e}"
            print(msg)
        cv2.putText(frame, msg[:60], (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("Inventory QR Scanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
