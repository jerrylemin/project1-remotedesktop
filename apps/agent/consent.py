from __future__ import annotations

from collections.abc import Callable
import os
from typing import Any


def require_consent_banner(machine_id: str, real_mode: bool) -> None:
    mode = "REAL" if real_mode else "FAKE"
    print(f"TelePC agent {machine_id} running in {mode} mode.")
    print("Consent required: this machine shows visible remote-control status while connected.")


def confirm_danger_action(action: str, confirmation: str) -> bool:
    return confirmation == "CONFIRM" and action in {"shutdown", "restart", "webcam", "file_exec"}


def _tkinter_popup(request: dict[str, Any], timeout_seconds: int) -> str:
    import tkinter as tk

    result = {"decision": "timeout"}
    root = tk.Tk()
    root.title("TelePC control request")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    action = request.get("command_type") or request.get("action_type") or "remote control"
    requester = request.get("requested_by") or "unknown user"
    machine = request.get("machine_id") or "this machine"
    reason = request.get("reason") or request.get("details") or ""

    if str(action).upper() == "KEYLOGGER_START":
        message = (
            "TelePC control request\n\n"
            f"User {requester} wants to start keyboard capture on this computer for lab demonstration.\n\n"
            "Only approve this if this is an authorized class/lab session.\n\n"
            f"This request expires in {timeout_seconds} seconds."
        )
    else:
        message = (
            "TelePC control request\n\n"
            f"User {requester} wants to run {action} on {machine}.\n\n"
            f"Details: {reason}\n\n"
            f"This request expires in {timeout_seconds} seconds."
        )
    tk.Label(root, text=message, justify="left", padx=20, pady=16, width=52).pack()
    buttons = tk.Frame(root, padx=20, pady=12)
    buttons.pack(fill="x")

    def decide(decision: str) -> None:
        result["decision"] = decision
        root.destroy()

    tk.Button(buttons, text="Yes", width=12, command=lambda: decide("approved")).pack(side="left", padx=8)
    tk.Button(buttons, text="No", width=12, command=lambda: decide("denied")).pack(side="right", padx=8)
    root.after(max(1, timeout_seconds) * 1000, lambda: decide("timeout"))
    root.mainloop()
    return result["decision"]


def show_consent_popup(
    request: dict[str, Any],
    timeout_seconds: int = 15,
    popup_runner: Callable[[dict[str, Any], int], str] | None = None,
) -> dict[str, str]:
    runner = popup_runner or _tkinter_popup
    try:
        decision = runner(request, timeout_seconds)
    except Exception:
        decision = "denied"
    if decision not in {"approved", "denied", "timeout"}:
        decision = "denied"
    return {"consent_id": str(request.get("id") or request.get("consent_id") or ""), "decision": decision}


def display_consent_prompt(request: dict[str, Any]) -> dict[str, str]:
    if "PYTEST_CURRENT_TEST" not in os.environ:
        return show_consent_popup(request, timeout_seconds=15)
    print("")
    print("TelePC consent request")
    print(f"Machine: {request.get('machine_id')}")
    print(f"Requester: {request.get('requested_by')}")
    print(f"Command: {request.get('command_type')}")
    print(f"Reason: {request.get('reason')}")
    print(f"Expires: {request.get('expires_at')}")
    try:
        answer = input("Type approve or deny: ").strip().lower()
    except (EOFError, TimeoutError):
        answer = "deny"
    decision = "approved" if answer == "approve" else "denied"
    return {"consent_id": str(request.get("id") or ""), "decision": decision}

