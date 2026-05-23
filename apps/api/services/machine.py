from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import EnrollToken, Machine, MachineSecret
from apps.api.services.audit import record_audit
from shared.crypto import hash_secret, random_secret, verify_secret
from shared.time_utils import utc_now


async def create_enroll_token(db: AsyncSession, created_by: int | None = None) -> str:
    token = random_secret(24)
    db.add(EnrollToken(id=str(uuid4()), token_hash=hash_secret(token), created_by=created_by))
    await db.flush()
    return token


async def enroll_machine(
    db: AsyncSession,
    *,
    enroll_token: str,
    hostname: str,
    os_name: str,
    username: str,
) -> tuple[Machine, str] | None:
    tokens = (await db.execute(select(EnrollToken).where(EnrollToken.used_at.is_(None)))).scalars().all()
    token_row = next((row for row in tokens if verify_secret(enroll_token, row.token_hash)), None)
    if token_row is None:
        return None
    machine_id = str(uuid4())
    machine_secret = random_secret(32)
    machine = Machine(
        machine_id=machine_id,
        hostname=hostname,
        os=os_name,
        username=username,
        status="online",
        last_seen=utc_now(),
    )
    token_row.used_at = utc_now()
    db.add(machine)
    db.add(MachineSecret(machine_id=machine_id, secret_hash=hash_secret(machine_secret)))
    await db.flush()
    return machine, machine_secret


async def list_machines(db: AsyncSession) -> list[Machine]:
    result = await db.execute(select(Machine).order_by(Machine.hostname))
    return list(result.scalars().all())


async def get_machine(db: AsyncSession, machine_id: str) -> Machine | None:
    return await db.scalar(select(Machine).where(Machine.machine_id == machine_id))


async def upsert_machine_status(
    db: AsyncSession,
    *,
    machine_id: str,
    status: str,
    hostname: str | None = None,
    os_name: str | None = None,
    username: str | None = None,
) -> Machine:
    machine = await get_machine(db, machine_id)
    if machine is None:
        machine = Machine(
            machine_id=machine_id,
            hostname=hostname or machine_id,
            os=os_name or "unknown",
            username=username or "unknown",
            status=status,
            last_seen=utc_now() if status == "online" else None,
        )
        db.add(machine)
        previous = None
    else:
        previous = machine.status
        if hostname:
            machine.hostname = hostname
        if os_name:
            machine.os = os_name
        if username:
            machine.username = username
        machine.status = status
        if status == "online":
            machine.last_seen = utc_now()
    if previous != status:
        await record_audit(
            db,
            event_type=f"agent_{status}",
            summary=f"Agent marked {status}",
            actor_type="system",
            machine_id=machine_id,
            metadata={"previous_status": previous, "new_status": status},
        )
    await db.flush()
    return machine
