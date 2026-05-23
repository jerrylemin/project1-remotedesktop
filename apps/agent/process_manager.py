from __future__ import annotations

from typing import Any


def list_processes() -> list[dict[str, Any]]:
    try:
        import psutil
    except ImportError:
        return [{"pid": 1, "name": "fake-system", "status": "running"}]
    rows = []
    for proc in psutil.process_iter(["pid", "name", "status"]):
        rows.append(proc.info)
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
    proc.terminate()
    return {"pid": pid, "stopped": True}

