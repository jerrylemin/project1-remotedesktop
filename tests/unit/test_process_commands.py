from __future__ import annotations

import pytest

from apps.agent.config import AgentSettings
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

