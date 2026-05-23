from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.agent.app_manager import list_applications
from apps.agent.input_demo import handle_input_event
from apps.agent.job_runner import run_job
from apps.agent.process_manager import list_processes
from apps.agent.sandbox import job_sandbox


async def handle_command(machine_id: str, command: dict[str, Any], sandbox_root: Path) -> dict[str, Any]:
    action = command.get("action")
    if action == "list_processes":
        return {"processes": list_processes()}
    if action == "list_applications":
        return {"applications": list_applications()}
    if action == "input_event":
        return handle_input_event(command)
    if action == "run_job":
        job_id = command["job_id"]
        cwd = job_sandbox(sandbox_root, machine_id, job_id)
        return await run_job(command["command"], cwd, command.get("timeout"))
    raise ValueError(f"unsupported command: {action}")

