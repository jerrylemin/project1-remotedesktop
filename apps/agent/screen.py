from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw


def fake_jpeg_frame(label: str = "TelePC Fake Agent") -> str:
    image = Image.new("RGB", (640, 360), color=(28, 34, 40))
    draw = ImageDraw.Draw(image)
    draw.rectangle((24, 24, 616, 336), outline=(64, 180, 160), width=4)
    draw.text((48, 56), label, fill=(245, 245, 245))
    draw.text((48, 96), "Consent visible - demo frame only", fill=(160, 220, 210))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=75)
    return base64.b64encode(buffer.getvalue()).decode()


def real_jpeg_frame() -> str:
    try:
        import mss
    except ImportError:
        return fake_jpeg_frame("mss unavailable")
    with mss.mss() as sct:
        shot = sct.grab(sct.monitors[1])
        image = Image.frombytes("RGB", shot.size, shot.rgb)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=65)
    return base64.b64encode(buffer.getvalue()).decode()

