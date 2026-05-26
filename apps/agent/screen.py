from __future__ import annotations

import base64
import io
import os
from typing import Any

from PIL import Image, ImageDraw
from shared.time_utils import utc_iso


def fake_jpeg_frame(label: str = "TelePC Fake Agent") -> str:
    image = Image.new("RGB", (640, 360), color=(28, 34, 40))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 616, 336), outline=(64, 180, 160), width=4)
    draw.text((48, 56), label, fill=(245, 245, 245))
    draw.text((48, 96), "Consent visible - demo frame only", fill=(160, 220, 210))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode()


def screen_fps() -> int:
    value = int(os.getenv("TELEPC_SCREEN_FPS", "5"))
    return value if value in {1, 5, 10} else 5


def jpeg_quality() -> int:
    value = int(os.getenv("TELEPC_SCREEN_JPEG_QUALITY", "60"))
    return max(20, min(95, value))


def real_jpeg_frame() -> str:
    try:
        import mss
    except ImportError:
        try:
            from PIL import ImageGrab
        except ImportError:
            return fake_jpeg_frame("mss and PIL ImageGrab unavailable")
        image = ImageGrab.grab()
    else:
        with mss.mss() as sct:
            shot = sct.grab(sct.monitors[1])
            image = Image.frombytes("RGB", shot.size, shot.rgb)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=jpeg_quality())
    return base64.b64encode(buffer.getvalue()).decode()


def frame_payload(
    data_b64: str,
    *,
    machine_id: str,
    session_id: str | None = None,
    width: int = 640,
    height: int = 360,
    frame_no: int = 1,
) -> dict[str, Any]:
    return {
        "type": "screen_frame",
        "machine_id": machine_id,
        "session_id": session_id,
        "width": width,
        "height": height,
        "mime": "image/jpeg",
        "data": data_b64,
        "jpeg_b64": data_b64,
        "frame_no": frame_no,
        "created_at": utc_iso(),
    }
