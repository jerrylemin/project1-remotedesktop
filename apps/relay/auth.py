from __future__ import annotations

from dataclasses import dataclass

from apps.api.security import decode_access_token
from apps.relay.api_client import validate_machine_secret
from shared.crypto import hash_secret


def validate_admin_token(token: str) -> dict:
    return decode_access_token(token)


@dataclass(frozen=True)
class MachineIdentity:
    machine_id: str
    status: str


def hash_machine_secret(raw_secret: str) -> str:
    return hash_secret(raw_secret)


async def verify_machine_secret(machine_id: str, raw_secret: str) -> bool:
    return await validate_agent_secret(machine_id, raw_secret)


async def require_valid_machine(machine_id: str, raw_secret: str) -> MachineIdentity:
    result = await validate_machine_secret(machine_id, raw_secret)
    if result is None:
        raise PermissionError("invalid machine credentials")
    return MachineIdentity(machine_id=result["machine_id"], status=result.get("status", "online"))


async def validate_agent_secret(machine_id: str, machine_secret: str) -> bool:
    if not machine_id or not machine_secret:
        return False
    try:
        await require_valid_machine(machine_id, machine_secret)
    except PermissionError:
        return False
    return True

