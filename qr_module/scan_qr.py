"""
scan_qr.py
FR-001 / FR-002: contactless check-in / check-out via camera scan,
with real-time status update in the database (NFR-001: <2s per scan).

Run directly for a live webcam demo:
    python -m qr_module.scan_qr --action check_out --user demo_user

Press 'q' to quit the video window.
"""

import argparse
import time

import cv2
from pyzbar.pyzbar import decode

from qr_module.models import get_item, init_db, record_scan

# Simple debounce so the same QR isn't scanned dozens of times per second
SCAN_COOLDOWN_SECONDS = 2.0


def scan_from_frame(frame):
    """Decode any QR codes visible in a single OpenCV frame."""
    decoded = decode(frame)
    return [obj.data.decode("utf-8") for obj in decoded]


def draw_box(frame, obj):
    points = obj.polygon
    if len(points) == 4:
        pts = [(p.x, p.y) for p in points]
        for i in range(4):
            cv2.line(frame, pts[i], pts[(i + 1) % 4], (0, 255, 0), 2)


def run_live_scanner(action: str, user: str | None = None, camera_index: int = 0):
    init_db()
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError("Could not open camera. Check camera_index / permissions.")

    last_scan_time = {}

    print(f"Scanner running in '{action}' mode. Press 'q' to quit.")
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break

            for obj in decode(frame):
                item_id = obj.data.decode("utf-8")
                draw_box(frame, obj)

                now = time.time()
                if now - last_scan_time.get(item_id, 0) < SCAN_COOLDOWN_SECONDS:
                    continue
                last_scan_time[item_id] = now

                item = get_item(item_id)
                if item is None:
                    print(f"[!] Unknown item_id scanned: {item_id}")
                    continue

                updated = record_scan(item_id, action, user)
                print(f"[OK] {item_id} -> {updated['status']} ({action})")

            cv2.imshow("Inventory QR Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live QR check-in/check-out scanner")
    parser.add_argument("--action", choices=["check_in", "check_out"], required=True)
    parser.add_argument("--user", default=None, help="User ID issuing/returning the item")
    parser.add_argument("--camera-index", type=int, default=0)
    args = parser.parse_args()

    run_live_scanner(args.action, args.user, args.camera_index)
