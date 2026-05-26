from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.agent.providers import AgentProviders, build_providers

PROTECTED_PROCESS_NAMES = {"lsass.exe", "winlogon.exe", "csrss.exe", "services.exe", "system", "registry"}


async def handle_command(machine_id: str, command: dict[str, Any], sandbox_root: Path, providers: AgentProviders | None = None) -> dict[str, Any]:
    providers = providers or build_providers("fake")
    action = command.get("action")
    if action == "list_processes":
        return {"processes": providers.processes.list_processes()}
    if action == "list_applications":
        return {"applications": providers.apps.list_applications()}
    if action == "start_application":
        return providers.apps.start_application(command["command"])
    if action == "stop_application":
        return providers.apps.stop_application(command["name"], bool(command.get("confirm")))
    if action == "stop_process":
        process_name = str(command.get("name") or "").lower()
        if process_name in PROTECTED_PROCESS_NAMES:
            raise PermissionError("protected process cannot be stopped")
        return providers.processes.stop_process(int(command["pid"]), bool(command.get("confirm")))
    if action == "input_event":
        return providers.input_controller.handle_input(command)
    if action == "webcam":
        return providers.webcam.set_webcam(bool(command.get("start")), bool(command.get("consent")))
    if action == "run_job":
        return await providers.sandbox.run(machine_id, sandbox_root, command)
    if action == "power":
        if not command.get("confirm") or not str(command.get("reason") or "").strip():
            raise PermissionError("power action requires confirmation and reason")
        return {"action": command.get("power_action"), "accepted": True, "demo_safe": True, "reason": command.get("reason")}
    raise ValueError(f"unsupported command: {action}")
