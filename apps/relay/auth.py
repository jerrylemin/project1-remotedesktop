from __future__ import annotations

from apps.api.security import decode_access_token


def validate_admin_token(token: str) -> dict:
    return decode_access_token(token)


def validate_agent_secret(machine_id: str, machine_secret: str) -> bool:
    return bool(machine_id and machine_secret)

