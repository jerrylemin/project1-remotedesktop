from __future__ import annotations

from pathlib import Path
from typing import Any

from apps.agent.consent import display_consent_prompt
from apps.agent.files import get_file, put_file
from apps.agent.key_capture import (
    export_key_capture_events,
    get_key_capture_events,
    start_key_capture_session,
    stop_key_capture_session,
)
from apps.agent.power_provider import run_power_action
from apps.agent.providers import AgentProviders, build_providers
from apps.agent.remote_files import discover_allowed_remote_folders, download_allowed_file, list_files_in_allowed_folder
from apps.agent import webcam as webcam_module

PROTECTED_PROCESS_NAMES = {"lsass.exe", "winlogon.exe", "csrss.exe", "services.exe", "system", "registry"}


async def handle_command(machine_id: str, command: dict[str, Any], sandbox_root: Path, providers: AgentProviders | None = None) -> dict[str, Any]:
    providers = providers or build_providers("fake")
    action = command.get("action")
    if action == "list_processes":
        return {"processes": providers.processes.list_processes()}
    if action == "list_applications":
        return {"applications": providers.apps.list_applications()}
    if action == "start_application":
        return providers.apps.start_application(str(command.get("app_key") or command.get("name") or command.get("command")))
    if action == "start_process":
        return providers.apps.start_application(command["process_key"])
    if action == "stop_application":
        return providers.apps.stop_application(command["name"], bool(command.get("confirm")))
    if action == "stop_process":
        process_name = str(command.get("name") or "").lower()
        if process_name in PROTECTED_PROCESS_NAMES:
            raise PermissionError("protected process cannot be stopped")
        return providers.processes.stop_process(int(command["pid"]), bool(command.get("confirm")))
    if action == "input_event":
        return providers.input_controller.handle_input(command)
    if action == "keylogger_start":
        return start_key_capture_session(
            int(command.get("ttl_seconds") or 60),
            {"approved": bool(command.get("consent"))},
            session_id=str(command.get("session_id") or ""),
            machine_id=machine_id,
            requested_by=str(command.get("requested_by") or ""),
        )
    if action == "keylogger_stop":
        return stop_key_capture_session(str(command["session_id"]))
    if action == "keylogger_events":
        return {"events": get_key_capture_events(str(command["session_id"]))}
    if action == "keylogger_export":
        data = export_key_capture_events(str(command["session_id"]), {"approved": bool(command.get("consent"))})
        return {"filename": f"keylogger-{command['session_id']}.csv", "content_base64": __import__("base64").b64encode(data).decode()}
    if action == "consent_request":
        return display_consent_prompt(dict(command["request"]))
    if action == "capture_screen":
        return providers.screen.capture_frame(machine_id, command.get("session_id"))
    if action in {"start_live_screen", "screen_start"}:
        return {"screen": "started", "fps": int(command.get("fps") or 5)}
    if action in {"stop_live_screen", "screen_stop"}:
        return {"screen": "stopped"}
    if action == "set_screen_fps":
        fps = int(command.get("fps") or 5)
        if fps not in {1, 5, 10}:
            raise ValueError("unsupported screen fps")
        return {"screen_fps": fps}
    if action == "file_put":
        return put_file(
            sandbox_root,
            machine_id,
            str(command["job_id"]),
            str(command["filename"]),
            str(command["content_base64"]),
            str(command.get("sha256") or "") or None,
        )
    if action == "file_get":
        return get_file(sandbox_root, machine_id, str(command["path"]))
    if action == "remote_files_roots":
        return {"allowed_folders": discover_allowed_remote_folders()}
    if action == "remote_files_list":
        if not command.get("consent"):
            raise PermissionError("file_list_consent_required")
        return {"files": list_files_in_allowed_folder(str(command["root_path"]), str(command.get("relative_path") or ""))}
    if action == "remote_file_download":
        if not command.get("consent"):
            raise PermissionError("file_download_consent_required")
        filename, data = download_allowed_file(str(command["root_path"]), str(command["relative_path"]))
        return {"filename": filename, "content_base64": __import__("base64").b64encode(data).decode()}
    if action == "webcam":
        start = bool(command.get("start"))
        result = providers.webcam.set_webcam(start, bool(command.get("consent")), command.get("device_id"))
        if start:
            result["webcam_frame"] = providers.webcam.snapshot(machine_id)
        return result
    if action == "webcam_devices":
        return {"webcam_devices": webcam_module.list_webcam_devices()}
    if action == "webcam_snapshot":
        if not command.get("consent"):
            raise PermissionError("webcam_consent_required")
        return {"webcam_frame": providers.webcam.snapshot(machine_id)}
    if action == "run_job":
        return await providers.sandbox.run(machine_id, sandbox_root, command)
    if action == "power":
        power_action = str(command.get("power_action") or "")
        reason = str(command.get("reason") or "")
        if not command.get("confirm"):
            raise PermissionError("power action requires confirmation")
        if power_action.lower() in {"restart", "shutdown"} and len(reason.strip()) < 5:
            raise PermissionError("power action requires reason of at least 5 characters")
        return run_power_action(power_action, reason)
    raise ValueError(f"unsupported command: {action}")
