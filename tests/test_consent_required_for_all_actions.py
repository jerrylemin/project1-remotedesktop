from __future__ import annotations

import pytest

from apps.relay.router import command_consent_binding


@pytest.mark.parametrize(
    ("payload", "command_type"),
    [
        ({"action": "start_application", "name": "chrome", "confirm": True}, "APPLICATION_START"),
        ({"action": "stop_application", "name": "chrome", "confirm": True}, "APPLICATION_STOP"),
        ({"action": "stop_process", "pid": 1, "name": "notepad.exe", "confirm": True}, "PROCESS_KILL"),
        ({"action": "capture_screen", "consent": True}, "SCREENSHOT"),
        ({"action": "screen_start", "mode": "live", "consent": True}, "LIVE_SCREEN_START"),
        ({"action": "screen_stop", "mode": "live", "consent": True}, "LIVE_SCREEN_STOP"),
        ({"action": "keylogger_start", "session_id": "s", "ttl_seconds": 30, "consent": True}, "KEYLOGGER_START"),
        ({"action": "keylogger_stop", "session_id": "s", "consent": True}, "KEYLOGGER_STOP"),
        ({"action": "keylogger_export", "session_id": "s", "consent": True}, "KEYLOGGER_EXPORT"),
        ({"action": "remote_files_list", "root_path": "C:\\Remote", "relative_path": "", "consent": True}, "FILE_LIST"),
        ({"action": "remote_file_download", "root_path": "C:\\Remote", "relative_path": "a", "consent": True}, "FILE_DOWNLOAD"),
        ({"action": "webcam_devices"}, "WEBCAM_ENUMERATE"),
        ({"action": "webcam", "start": True, "consent": True, "device_id": "camera-0"}, "WEBCAM_START"),
        ({"action": "webcam", "start": False, "consent": True}, "WEBCAM_STOP"),
        ({"action": "power", "power_action": "restart", "confirm": True, "reason": "test run"}, "POWER_RESTART"),
        ({"action": "power", "power_action": "shutdown", "confirm": True, "reason": "test run"}, "POWER_SHUTDOWN"),
    ],
)
def test_every_sensitive_relay_action_has_exact_consent_binding(payload: dict, command_type: str) -> None:
    binding = command_consent_binding(payload)

    assert binding is not None
    assert binding[0] == command_type
