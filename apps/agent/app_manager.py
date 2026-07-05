from __future__ import annotations

import subprocess
import os
from pathlib import Path
from typing import Any

from apps.agent.process_manager import PROTECTED

ALLOWED_APPLICATIONS: dict[str, dict[str, Any]] = {
    "zalo": {
        "display_name": "Zalo",
        "executable_names": ["Zalo.exe"],
        "start_paths": [[r"C:\Users\{user}\AppData\Local\Programs\Zalo\Zalo.exe"]],
    },
    "discord": {
        "display_name": "Discord",
        "executable_names": ["Discord.exe", "Update.exe"],
        "start_paths": [
            [r"C:\Users\{user}\AppData\Local\Discord\Update.exe", "--processStart", "Discord.exe"],
            ["Discord.exe"],
        ],
    },
    "vscode": {
        "display_name": "VSCode",
        "executable_names": ["Code.exe"],
        "start_paths": [[r"C:\Users\{user}\AppData\Local\Programs\Microsoft VS Code\Code.exe"], ["Code.exe"]],
    },
    "chrome": {
        "display_name": "Chrome",
        "executable_names": ["chrome.exe"],
        "start_paths": [[r"C:\Program Files\Google\Chrome\Application\chrome.exe"], [r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"], ["chrome.exe"]],
    },
    "notepad": {
        "display_name": "Notepad",
        "executable_names": ["notepad.exe"],
        "start_paths": [["notepad.exe"]],
    },
}


def list_allowed_applications() -> list[dict[str, Any]]:
    return [
        {
            "app_key": key,
            "display_name": app["display_name"],
            "executable_names": list(app["executable_names"]),
            "start_paths": list(app["start_paths"]),
            "is_enabled": True,
        }
        for key, app in ALLOWED_APPLICATIONS.items()
    ]


def list_applications() -> list[dict[str, Any]]:
    rows = {
        app["app_key"]: {
            "app_key": app["app_key"],
            "name": app["display_name"],
            "display_name": app["display_name"],
            "installed": False,
            "running": False,
            "status": "missing",
            "pid_list": [],
            "pids": [],
            "cpu_percent": 0.0,
            "cpu": 0.0,
            "start_allowed": False,
            "stop_allowed": False,
        }
        for app in list_allowed_applications()
    }
    try:
        import psutil
    except ImportError:
        return list(rows.values())
    executable_to_key = {
        executable.lower(): key
        for key, app in ALLOWED_APPLICATIONS.items()
        for executable in app["executable_names"]
    }
    for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_percent", "exe"]):
        info = proc.info
        name = str(info.get("name") or "unknown")
        key = executable_to_key.get(name.lower())
        if key is None:
            continue
        item = rows[key]
        item["installed"] = True
        item["running"] = True
        item["status"] = info.get("status") or "running"
        item["pid_list"].append(info.get("pid"))
        item["pids"] = item["pid_list"]
        item["cpu_percent"] += float(info.get("cpu_percent") or 0.0)
        item["cpu"] = item["cpu_percent"]
        item["start_allowed"] = False
        item["stop_allowed"] = True
    return list(rows.values())


def _allowed_command(name: str) -> list[str] | None:
    key = name.lower().removesuffix(".exe")
    app = ALLOWED_APPLICATIONS.get(key)
    if app is None:
        return None
    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    for template in app["start_paths"]:
        parts = [part.format(user=user) for part in template]
        executable = parts[0]
        if "\\" not in executable or Path(executable).exists():
            return parts
    return None


def start_application(command: str) -> dict[str, Any]:
    allowed = _allowed_command(command)
    if allowed is None:
        error = "not_in_allowlist" if command.lower().removesuffix(".exe") not in ALLOWED_APPLICATIONS else "APP_NOT_FOUND"
        return {"error": error, "name": command}
    proc = subprocess.Popen(allowed, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"pid": proc.pid, "name": command, "command": allowed[0]}


def stop_application(name: str, confirm: bool) -> dict[str, Any]:
    if not confirm:
        raise PermissionError("application stop requires confirmation")
    target_key = name.lower().removesuffix(".exe")
    if f"{target_key}.exe" in PROTECTED or target_key in PROTECTED:
        raise PermissionError("protected process cannot be stopped")
    app = ALLOWED_APPLICATIONS.get(target_key)
    if app is None:
        raise PermissionError("application not in whitelist")
    executable_names = {item.lower().removesuffix(".exe") for item in app["executable_names"]}
    try:
        import psutil
    except ImportError:
        return {"name": name, "stopped": 0, "fake": True}
    stopped = 0
    for proc in psutil.process_iter(["name"]):
        proc_name = str(proc.info.get("name") or "").lower().removesuffix(".exe")
        if proc_name in executable_names:
            proc.terminate()
            stopped += 1
    return {"name": name, "stopped": stopped}
