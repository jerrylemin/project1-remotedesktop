from __future__ import annotations

from pathlib import Path


def test_webcam_ui_has_no_static_camera_zero_fallback() -> None:
    html = Path("apps/api/templates/machine_detail.html").read_text(encoding="utf-8")
    js = Path("apps/api/static/js/machine_detail.js").read_text(encoding="utf-8")

    assert '<option value="camera-0">Camera 0</option>' not in html
    assert "Camera 0" not in js
    assert "start.disabled = true" in js


def test_webcam_ui_awaits_agent_device_result() -> None:
    js = Path("apps/api/static/js/machine_detail.js").read_text(encoding="utf-8")

    assert "WEBCAM_ENUMERATE" in js
    assert "apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/webcam/devices`)" in js
    assert "response.webcam_devices" in js
    assert "device.device_id" in js
