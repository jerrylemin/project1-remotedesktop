from __future__ import annotations

import math
from typing import Any

PROTECTED = {
    "system",
    "registry",
    "smss.exe",
    "csrss.exe",
    "wininit.exe",
    "winlogon.exe",
    "services.exe",
    "lsass.exe",
    "svchost.exe",
}


def list_processes() -> list[dict[str, Any]]:
    try:
        import psutil
    except ImportError:
        return [{"pid": 1, "name": "fake-system", "username": "demo", "cpu_percent": 0.0, "memory_mb": 0.0, "memory_percent": 0.0, "status": "running", "protected": False}]
    rows = []
    for proc in psutil.process_iter(["pid", "name", "username", "status", "cpu_percent", "memory_percent", "memory_info"]):
        try:
            info = proc.info
        except Exception:
            continue
        name = str(info.get("name") or "")
        rss = getattr(info.get("memory_info"), "rss", 0) or 0
        cpu = float(info.get("cpu_percent") or 0.0)
        memory = float(info.get("memory_percent") or 0.0)
        cpu = cpu if math.isfinite(cpu) and cpu >= 0 else 0.0
        memory = memory if math.isfinite(memory) and memory >= 0 else 0.0
        rows.append(
            {
                "pid": info.get("pid"),
                "name": name,
                "username": info.get("username") or "",
                "cpu_percent": cpu,
                "memory_mb": round(max(0, rss) / (1024 * 1024), 2),
                "memory_percent": round(memory, 2),
                "status": info.get("status") or "unknown",
                "protected": name.lower() in PROTECTED,
            }
        )
    return rows


def stop_process(pid: int, confirm: bool = False, expected_name: str | None = None) -> dict[str, Any]:
    if pid <= 0:
        raise ValueError("invalid pid")
    if not confirm:
        raise PermissionError("process stop requires confirmation")
    try:
        import psutil
    except ImportError:
        return {"pid": pid, "stopped": False, "fake": True}
    proc = psutil.Process(pid)
    name = (proc.name() or "").lower()
    if expected_name and name != expected_name.strip().lower():
        raise PermissionError("process identity changed after consent")
    if name in PROTECTED:
        raise PermissionError("protected process cannot be stopped")
    proc.terminate()
    return {"pid": pid, "name": name, "stopped": True}
