from __future__ import annotations

from apps.agent.power_provider import build_power_command, run_power_action


def test_default_power_is_demo_safe(monkeypatch) -> None:
    called = []
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: called.append(args))
    result = run_power_action("restart", "demo restart", real_power=False)
    assert result["demo_safe"] is True
    assert result["executed"] is False
    assert called == []


def test_real_provider_builds_restart_command() -> None:
    command = build_power_command("restart", "demo restart")
    assert command[:4] == ["shutdown", "/r", "/t", "30"]


def test_cancel_command_built() -> None:
    assert build_power_command("cancel") == ["shutdown", "/a"]
