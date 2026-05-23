from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import get_current_user, require_permission
from apps.api.models import User
from apps.api.schemas import AgentEnrollIn, AgentEnrollOut, EnrollTokenOut, MachineOut
from apps.api.services.audit import record_audit
from apps.api.services.machine import create_enroll_token, enroll_machine, get_machine, list_machines
from shared.enums import Permission

router = APIRouter(prefix="/api", tags=["machines"])


def machine_out(machine) -> MachineOut:
    return MachineOut(
        machine_id=machine.machine_id,
        hostname=machine.hostname,
        os=machine.os,
        username=machine.username,
        status=machine.status,
        last_seen=machine.last_seen,
    )


@router.get("/machines", response_model=list[MachineOut])
async def machines(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MACHINES_READ)),
) -> list[MachineOut]:
    return [machine_out(machine) for machine in await list_machines(db)]


@router.get("/machines/{machine_id}", response_model=MachineOut)
async def machine_detail(
    machine_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MACHINES_READ)),
) -> MachineOut:
    machine = await get_machine(db, machine_id)
    if machine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="machine not found")
    return machine_out(machine)


@router.post("/enroll-tokens", response_model=EnrollTokenOut)
async def enroll_token(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.ADMIN_MANAGE)),
) -> EnrollTokenOut:
    token = await create_enroll_token(db, user.id)
    await db.commit()
    return EnrollTokenOut(enroll_token=token)


@router.post("/agents/enroll", response_model=AgentEnrollOut)
async def agent_enroll(body: AgentEnrollIn, db: AsyncSession = Depends(get_db)) -> AgentEnrollOut:
    enrolled = await enroll_machine(
        db,
        enroll_token=body.enroll_token,
        hostname=body.hostname,
        os_name=body.os,
        username=body.username,
    )
    if enrolled is None:
        await record_audit(db, event_type="auth_failed", summary="Invalid enroll token", actor_type="agent")
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid enroll token")
    machine, secret = enrolled
    await record_audit(
        db,
        event_type="agent_enrolled",
        summary=f"{machine.hostname} enrolled",
        actor_type="agent",
        machine_id=machine.machine_id,
    )
    await db.commit()
    return AgentEnrollOut(machine_id=machine.machine_id, machine_secret=secret)

