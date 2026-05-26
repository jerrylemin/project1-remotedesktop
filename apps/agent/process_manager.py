from __future__ import annotations

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
        info = proc.info
        name = str(info.get("name") or "")
        rss = getattr(info.get("memory_info"), "rss", 0) or 0
        rows.append(
            {
                "pid": info.get("pid"),
                "name": name,
                "username": info.get("username") or "",
                "cpu_percent": float(info.get("cpu_percent") or 0.0),
                "memory_mb": round(rss / (1024 * 1024), 2),
                "memory_percent": round(float(info.get("memory_percent") or 0.0), 2),
                "status": info.get("status") or "unknown",
                "protected": name.lower() in PROTECTED,
            }
        )
    return rows


def stop_process(pid: int, confirm: bool = False) -> dict[str, Any]:
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
    if name in PROTECTED:
        raise PermissionError("protected process cannot be stopped")
    proc.terminate()
    return {"pid": pid, "name": name, "stopped": True}
