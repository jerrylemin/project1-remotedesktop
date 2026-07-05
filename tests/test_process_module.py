from __future__ import annotations

import sys
import types

import pytest

from apps.agent.process_manager import list_processes, stop_process


def test_pid_reuse_name_mismatch_is_rejected_without_terminating(monkeypatch) -> None:
    terminated = []

    class Process:
        def name(self) -> str:
            return "other.exe"

        def terminate(self) -> None:
            terminated.append(True)

    monkeypatch.setitem(sys.modules, "psutil", types.SimpleNamespace(Process=lambda _pid: Process()))

    with pytest.raises(PermissionError, match="identity changed"):
        stop_process(123, True, expected_name="notepad.exe")

    assert terminated == []


def test_process_list_skips_disappearing_process_and_normalizes_nan(monkeypatch) -> None:
    class BadProcess:
        @property
        def info(self):
            raise RuntimeError("process disappeared")

    class GoodProcess:
        info = {
            "pid": 7,
            "name": "worker.exe",
            "username": None,
            "status": "running",
            "cpu_percent": float("nan"),
            "memory_percent": -1,
            "memory_info": types.SimpleNamespace(rss=1024),
        }

    monkeypatch.setitem(sys.modules, "psutil", types.SimpleNamespace(process_iter=lambda _attrs: [BadProcess(), GoodProcess()]))

    rows = list_processes()

    assert rows == [
        {
            "pid": 7,
            "name": "worker.exe",
            "username": "",
            "cpu_percent": 0.0,
            "memory_mb": 0.0,
            "memory_percent": 0.0,
            "status": "running",
            "protected": False,
        }
    ]
