from __future__ import annotations

import pytest

from apps.agent.commands import handle_command
from apps.agent.providers import build_providers


def test_fake_provider_returns_frame_dict() -> None:
    frame = build_providers("fake").screen.capture_frame("m1", frame_no=42)
    for key in ["type", "machine_id", "width", "height", "mime", "data", "frame_no", "created_at"]:
        assert key in frame
    assert frame["type"] == "screen_frame"
    assert frame["mime"] == "image/jpeg"


@pytest.mark.asyncio
async def test_capture_screen_command_returns_frame(tmp_path) -> None:
    result = await handle_command("m1", {"action": "capture_screen"}, tmp_path, build_providers("fake"))
    assert result["machine_id"] == "m1"
    assert result["data"]
