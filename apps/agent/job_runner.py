from __future__ import annotations

import asyncio
import shlex
from pathlib import Path
from typing import Any

from apps.agent.config import AgentSettings, get_agent_settings
from shared.time_utils import utc_iso


class JobPolicyError(ValueError):
    pass


def validate_command(command: str, settings: AgentSettings | None = None) -> list[str]:
    settings = settings or get_agent_settings()
    parts = shlex.split(command, posix=False)
    if not parts:
        raise JobPolicyError("empty command")
    runner = Path(parts[0]).name.lower().removesuffix(".exe")
    if runner not in settings.runners:
        raise JobPolicyError("runner blocked by allowlist")
    return parts


async def run_job(command: str, cwd: Path, timeout: int | None = None, settings: AgentSettings | None = None) -> dict[str, Any]:
    settings = settings or get_agent_settings()
    args = validate_command(command, settings)
    timeout = timeout or settings.job_timeout_seconds
    started_at = utc_iso()
    try:
        process = await asyncio.create_subprocess_exec(
            *args,
            cwd=str(cwd),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
        exit_code = process.returncode
    except asyncio.TimeoutError:
        process.kill()
        stdout, stderr = await process.communicate()
        exit_code = -1
    return {
        "command": command,
        "cwd": str(cwd),
        "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": utc_iso(),
    }

