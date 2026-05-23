from __future__ import annotations


def require_consent_banner(machine_id: str, real_mode: bool) -> None:
    mode = "REAL" if real_mode else "FAKE"
    print(f"TelePC agent {machine_id} running in {mode} mode.")
    print("Consent required: this machine shows visible remote-control status while connected.")


def confirm_danger_action(action: str, confirmation: str) -> bool:
    return confirmation == "CONFIRM" and action in {"shutdown", "restart", "webcam", "file_exec"}

