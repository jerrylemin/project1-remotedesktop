from __future__ import annotations

import types

from apps.agent.commands import handle_command
from apps.agent.webcam import list_webcam_devices


def test_builtin_and_usb_cameras_appear(monkeypatch) -> None:
    class Capture:
        def __init__(self, index: int, *_args) -> None:
            self.index = index

        def isOpened(self) -> bool:
            return self.index in {0, 2}

        def release(self) -> None:
            return None

    cv2 = types.SimpleNamespace(VideoCapture=Capture, CAP_DSHOW=700)
    monkeypatch.setitem(__import__("sys").modules, "cv2", cv2)

    devices = list_webcam_devices(max_devices=3)

    assert [device["index"] for device in devices] == [0, 2]
    assert devices[0]["device_id"] == "camera-0"
    assert devices[1]["name"] == "Camera 2"


async def test_agent_lists_webcam_devices(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("apps.agent.webcam.list_webcam_devices", lambda: [{"device_id": "camera-0", "index": 0, "name": "Camera 0", "backend": "opencv", "available": True}])

    result = await handle_command("m1", {"action": "webcam_devices"}, tmp_path)

    assert result["webcam_devices"][0]["device_id"] == "camera-0"
