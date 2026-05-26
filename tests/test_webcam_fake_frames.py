from __future__ import annotations

import pytest

from apps.agent.commands import handle_command
from apps.agent.providers import ProviderError, build_providers
from apps.agent.webcam import fake_webcam_frame


def test_fake_webcam_frame_schema() -> None:
    frame = fake_webcam_frame("m1")
    assert frame["type"] == "webcam_frame"
    assert frame["mime"] == "image/jpeg"
    assert frame["data"]


@pytest.mark.asyncio
async def test_webcam_start_without_consent_rejected(tmp_path) -> None:
    with pytest.raises(ProviderError):
        await handle_command("m1", {"action": "webcam", "start": True, "consent": False}, tmp_path, build_providers("fake"))
