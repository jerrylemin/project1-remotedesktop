from __future__ import annotations

import subprocess
import os
from pathlib import Path
from typing import Any

from apps.agent.config import APP_ALLOWLIST
from apps.agent.process_manager import PROTECTED


def list_applications() -> list[dict[str, Any]]:
    try:
        import psutil
    except ImportError:
        return [{"name": name, "pids": [], "status": "allowed", "cpu_percent": 0.0, "memory_percent": 0.0, "exe": command} for name, command in sorted(APP_ALLOWLIST.items())]
    grouped: dict[str, dict[str, Any]] = {}
    for proc in psutil.process_iter(["pid", "name", "status", "cpu_percent", "memory_percent", "exe"]):
        info = proc.info
        name = str(info.get("name") or "unknown")
        key = name.lower()
        item = grouped.setdefault(
            key,
            {"name": name, "pids": [], "status": info.get("status") or "unknown", "cpu_percent": 0.0, "memory_percent": 0.0, "exe": info.get("exe") or ""},
        )
        item["pids"].append(info.get("pid"))
        item["cpu_percent"] += float(info.get("cpu_percent") or 0.0)
        item["memory_percent"] += float(info.get("memory_percent") or 0.0)
        if not item["exe"] and info.get("exe"):
            item["exe"] = info.get("exe")
    return sorted(grouped.values(), key=lambda row: str(row["name"]).lower())


def _allowed_command(name: str) -> str | None:
    key = name.lower().removesuffix(".exe")
    template = APP_ALLOWLIST.get(key)
    if template is None:
        return None
    user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    command = template.format(user=user)
    if "\\" in command and not Path(command).exists():
        return None
    return command


def start_application(command: str) -> dict[str, Any]:
    allowed = _allowed_command(command)
    if allowed is None:
        return {"error": "not_in_allowlist", "name": command}
    proc = subprocess.Popen([allowed], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"pid": proc.pid, "name": command, "command": allowed}


def stop_application(name: str, confirm: bool) -> dict[str, Any]:
    if not confirm:
        raise PermissionError("application stop requires confirmation")
    target = name.lower().removesuffix(".exe")
    if f"{target}.exe" in PROTECTED or target in PROTECTED:
        raise PermissionError("protected process cannot be stopped")
    try:
        import psutil
    except ImportError:
        return {"name": name, "stopped": 0, "fake": True}
    stopped = 0
    for proc in psutil.process_iter(["name"]):
        proc_name = str(proc.info.get("name") or "").lower().removesuffix(".exe")
        if proc_name == target:
            proc.terminate()
            stopped += 1
    return {"name": name, "stopped": stopped}
