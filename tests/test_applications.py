from __future__ import annotations

import types

from apps.agent.app_manager import list_applications, start_application, stop_application


def test_start_not_in_whitelist_rejected() -> None:
    assert start_application("cmd")["error"] == "not_in_allowlist"


def test_stop_protected_process_name_blocked() -> None:
    try:
        stop_application("lsass.exe", True)
    except PermissionError as exc:
        assert "protected" in str(exc)


def test_list_applications_returns_required_whitelist_only(monkeypatch) -> None:
    class Proc:
        info = {"pid": 1, "name": "notepad.exe", "status": "running", "cpu_percent": 1.5, "memory_percent": 2.0, "exe": "notepad.exe"}

    monkeypatch.setitem(__import__("sys").modules, "psutil", types.SimpleNamespace(process_iter=lambda attrs: [Proc()]))
    rows = list_applications()
    assert [row["app_key"] for row in rows] == ["zalo", "discord", "vscode", "chrome", "notepad"]
    notepad = rows[-1]
    assert notepad["display_name"] == "Notepad"
    assert notepad["installed"] is True
    assert notepad["running"] is True
    assert notepad["pid_list"] == [1]
    assert notepad["cpu_percent"] == 1.5


def test_missing_whitelist_app_still_appears(monkeypatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "psutil", types.SimpleNamespace(process_iter=lambda attrs: []))

    rows = list_applications()

    chrome = next(row for row in rows if row["app_key"] == "chrome")
    assert chrome["installed"] is False
    assert chrome["running"] is False
    assert chrome["cpu_percent"] == 0.0


def test_windows_application_path_with_spaces_stays_one_argument(monkeypatch) -> None:
    launched = []

    def fake_popen(args, **kwargs):
        launched.append(args)
        return types.SimpleNamespace(pid=42)

    monkeypatch.setattr("apps.agent.app_manager.Path.exists", lambda path: str(path).endswith("chrome.exe"))
    monkeypatch.setattr("apps.agent.app_manager.subprocess.Popen", fake_popen)

    result = start_application("chrome")

    assert result["pid"] == 42
    assert launched == [[r"C:\Program Files\Google\Chrome\Application\chrome.exe"]]
