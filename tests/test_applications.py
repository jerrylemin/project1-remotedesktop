from __future__ import annotations

import types

from apps.agent.app_manager import list_applications, start_application, stop_application


def test_start_not_in_allowlist_rejected() -> None:
    assert start_application("cmd")["error"] == "not_in_allowlist"


def test_stop_protected_process_name_blocked() -> None:
    try:
        stop_application("lsass.exe", True)
    except PermissionError as exc:
        assert "protected" in str(exc)


def test_list_applications_groups_psutil(monkeypatch) -> None:
    class Proc:
        info = {"pid": 1, "name": "notepad.exe", "status": "running", "cpu_percent": 1.5, "memory_percent": 2.0, "exe": "notepad.exe"}

    monkeypatch.setitem(__import__("sys").modules, "psutil", types.SimpleNamespace(process_iter=lambda attrs: [Proc()]))
    rows = list_applications()
    assert rows[0]["name"] == "notepad.exe"
    assert rows[0]["pids"] == [1]
