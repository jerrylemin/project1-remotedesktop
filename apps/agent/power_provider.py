from __future__ import annotations

import os
import subprocess
from typing import Any


REAL_POWER = os.getenv("TELEPC_ENABLE_REAL_POWER", "false").lower() == "true"

COMMANDS = {
    "restart": ["shutdown", "/r", "/t", "30", "/c"],
    "shutdown": ["shutdown", "/s", "/t", "30", "/c"],
    "cancel": ["shutdown", "/a"],
    "lock": ["rundll32.exe", "user32.dll,LockWorkStation"],
}


def build_power_command(action: str, reason: str = "") -> list[str]:
    action = action.lower()
    if action not in COMMANDS:
        raise ValueError("unsupported power action")
    command = list(COMMANDS[action])
    if action in {"restart", "shutdown"}:
        command.append(f"TelePC: {reason}")
    return command


def run_power_action(action: str, reason: str = "", *, real_power: bool | None = None) -> dict[str, Any]:
    action = action.lower()
    if action in {"restart", "shutdown"} and len(reason.strip()) < 5:
        raise PermissionError("power action requires a reason of at least 5 characters")
    enabled = REAL_POWER if real_power is None else real_power
    command = build_power_command(action, reason)
    if not enabled:
        return {"action": action, "demo_safe": True, "command_built": " ".join(command), "executed": False, "real_power_enabled": False}
    print("TelePC REAL POWER ENABLED: command will execute after the Windows safety delay.")
    subprocess.run(command, check=False)
    return {"action": action, "demo_safe": False, "command_built": " ".join(command), "executed": True, "real_power_enabled": True}
