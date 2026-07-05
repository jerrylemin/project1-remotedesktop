from __future__ import annotations

import subprocess

import main


def test_server_children_inherit_enabled_real_control_defaults(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_popen(*args, **kwargs):
        captured.update(kwargs["env"])
        return object()

    monkeypatch.delenv("TELEPC_ENABLE_REAL_INPUT", raising=False)
    monkeypatch.delenv("TELEPC_ENABLE_REAL_POWER", raising=False)
    monkeypatch.delenv("TELEPC_REAL_MODE_CONFIRMED", raising=False)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    main.start_child("api", ["-m", "apps.api.main"])

    assert captured["TELEPC_ENABLE_REAL_INPUT"] == "true"
    assert captured["TELEPC_ENABLE_REAL_POWER"] == "true"
    assert captured["TELEPC_REAL_MODE_CONFIRMED"] == "TELEPC_LAB_AUTHORIZED"
