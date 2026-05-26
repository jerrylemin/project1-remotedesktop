from __future__ import annotations

import types

import pytest

from apps.agent.process_manager import stop_process


def test_lsass_blocked_at_agent_layer(monkeypatch) -> None:
    class Proc:
        def __init__(self, pid: int) -> None:
            self.pid = pid

        def name(self) -> str:
            return "lsass.exe"

    monkeypatch.setitem(__import__("sys").modules, "psutil", types.SimpleNamespace(Process=Proc))
    with pytest.raises(PermissionError):
        stop_process(500, True)
