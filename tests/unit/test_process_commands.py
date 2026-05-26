from __future__ import annotations

import pytest

from apps.agent.config import AgentSettings
from apps.agent.commands import handle_command
from apps.agent.job_runner import JobPolicyError, validate_command
from apps.agent.process_manager import stop_process


def test_runner_allowlist_enforced(tmp_path) -> None:
    settings = AgentSettings(sandbox_root=tmp_path, runner_allowlist="python")
    assert validate_command("python -V", settings)[0].lower() == "python"
    with pytest.raises(JobPolicyError):
        validate_command("powershell Get-Process", settings)


def test_pid_validation_and_confirmation() -> None:
    with pytest.raises(ValueError):
        stop_process(0, confirm=True)
    with pytest.raises(PermissionError):
        stop_process(1234, confirm=False)


async def test_agent_denies_protected_process_stop(tmp_path) -> None:
    with pytest.raises(PermissionError):
        await handle_command("m1", {"action": "stop_process", "pid": 500, "name": "lsass.exe", "confirm": True}, tmp_path)


async def test_agent_allows_power_cancel_without_reason(tmp_path) -> None:
    result = await handle_command("m1", {"action": "power", "power_action": "cancel", "confirm": True}, tmp_path)
    assert result["action"] == "cancel"
    assert result["demo_safe"] is True
