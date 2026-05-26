from __future__ import annotations

import pytest

from apps.agent.job_runner import JobPolicyError, command_from_schema, run_job


def test_unknown_command_type_rejected() -> None:
    with pytest.raises(JobPolicyError):
        command_from_schema({"command_type": "exe", "args": []})


@pytest.mark.asyncio
async def test_fake_python_job_returns_stdout(tmp_path) -> None:
    result = await run_job('python -c "print(123)"', tmp_path, timeout=10)
    assert result["exit_code"] == 0
    assert "123" in result["stdout"]
    assert result["timed_out"] is False
