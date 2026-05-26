from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image, ImageDraw
from shared.time_utils import utc_iso


def webcam_status(start: bool, consent: bool) -> dict[str, object]:
    if start and not consent:
        raise PermissionError("webcam requires explicit consent")
    return {"webcam": "started" if start else "stopped", "consent": consent}


def fake_webcam_frame(machine_id: str = "fake-machine-001", frame_no: int = 1) -> dict[str, Any]:
    image = Image.new("RGB", (640, 360), color=(30, 28, 42))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 616, 336), outline=(220, 170, 70), width=4)
    draw.text((48, 56), "TelePC webcam demo frame", fill=(245, 245, 245))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=70)
    data = base64.b64encode(buffer.getvalue()).decode()
    return {
        "type": "webcam_frame",
        "machine_id": machine_id,
        "session_id": None,
        "width": 640,
        "height": 360,
        "mime": "image/jpeg",
        "data": data,
        "jpeg_b64": data,
        "frame_no": frame_no,
        "created_at": utc_iso(),
    }


def cv2_snapshot(machine_id: str, frame_no: int = 1) -> dict[str, Any]:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("cv2_not_installed: pip install opencv-python") from exc
    capture = cv2.VideoCapture(0)
    try:
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError("webcam frame unavailable")
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise RuntimeError("webcam jpeg encode failed")
        data = base64.b64encode(encoded.tobytes()).decode()
        height, width = frame.shape[:2]
        return {
            "type": "webcam_frame",
            "machine_id": machine_id,
            "session_id": None,
            "width": width,
            "height": height,
            "mime": "image/jpeg",
            "data": data,
            "jpeg_b64": data,
            "frame_no": frame_no,
            "created_at": utc_iso(),
        }
    finally:
        capture.release()
