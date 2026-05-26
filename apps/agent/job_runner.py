from __future__ import annotations

import asyncio
import shlex
from pathlib import Path
from typing import Any

from apps.agent.config import AgentSettings, get_agent_settings
from shared.time_utils import utc_iso

ALLOWED_COMMANDS = {"python": "python", "powershell": "powershell.exe", "pwsh": "pwsh", "cmd": "cmd.exe"}
OUTPUT_LIMIT = 64 * 1024


class JobPolicyError(ValueError):
    pass


def validate_command(command: str, settings: AgentSettings | None = None) -> list[str]:
    settings = settings or get_agent_settings()
    parts = shlex.split(command, posix=True)
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
    timed_out = False
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
        timed_out = True
        process.kill()
        stdout, stderr = await process.communicate()
        exit_code = -1
    stdout_text = stdout.decode(errors="replace")
    stderr_text = stderr.decode(errors="replace")
    if len(stdout_text) > OUTPUT_LIMIT:
        stdout_text = stdout_text[:OUTPUT_LIMIT] + "\n[truncated]"
    if len(stderr_text) > OUTPUT_LIMIT:
        stderr_text = stderr_text[:OUTPUT_LIMIT] + "\n[truncated]"
    return {
        "command": command,
        "cwd": str(cwd),
        "stdout": stdout_text,
        "stderr": stderr_text,
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": utc_iso(),
        "timed_out": timed_out,
    }


def command_from_schema(payload: dict[str, Any]) -> str:
    command_type = str(payload.get("command_type") or "").lower()
    if not command_type:
        return str(payload.get("command") or "")
    if command_type not in ALLOWED_COMMANDS:
        raise JobPolicyError("unknown command type")
    args = [str(item) for item in payload.get("args") or []]
    return " ".join([ALLOWED_COMMANDS[command_type], *args])
