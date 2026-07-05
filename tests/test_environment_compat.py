from __future__ import annotations

import sys

from apps.agent.config import AgentSettings
from apps.agent.screen import jpeg_quality, screen_fps
from apps.agent.webcam import webcam_fps, webcam_height, webcam_jpeg_quality, webcam_width


def test_supported_python_and_production_safe_agent_default() -> None:
    assert sys.version_info >= (3, 11)
    assert AgentSettings(_env_file=None).agent_mode == "real"


def test_invalid_capture_tuning_falls_back_safely(monkeypatch) -> None:
    for name in (
        "TELEPC_SCREEN_FPS",
        "TELEPC_SCREEN_JPEG_QUALITY",
        "TELEPC_WEBCAM_FPS",
        "TELEPC_WEBCAM_JPEG_QUALITY",
        "TELEPC_WEBCAM_WIDTH",
        "TELEPC_WEBCAM_HEIGHT",
    ):
        monkeypatch.setenv(name, "not-an-integer")

    assert screen_fps() == 5
    assert jpeg_quality() == 60
    assert webcam_fps() == 30
    assert webcam_jpeg_quality() == 25
    assert webcam_width() == 640
    assert webcam_height() == 360
