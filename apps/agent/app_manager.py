from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from apps.agent.config import get_agent_settings


def list_applications() -> list[dict[str, str]]:
    return [{"name": app, "allowed": "true"} for app in sorted(get_agent_settings().apps)]


def start_application(command: str) -> dict[str, Any]:
    settings = get_agent_settings()
    exe = Path(command.split()[0]).name.lower().removesuffix(".exe")
    if exe not in settings.apps:
        raise PermissionError("application blocked by allowlist")
    proc = subprocess.Popen(command.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"pid": proc.pid, "command": command}

