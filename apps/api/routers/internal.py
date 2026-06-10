from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps_internal import require_internal_secret
from apps.api.services.audit import record_audit
from apps.api.services.machine import require_valid_machine, upsert_machine_status
from apps.api.services.session import get_active_control_session, release_active_control_session

router = APIRouter(prefix="/internal", tags=["internal"], dependencies=[Depends(require_internal_secret)])


class InternalAuditIn(BaseModel):
    event_type: str
    summary: str
    actor_type: str = "system"
    machine_id: str | None = None
    session_id: str | None = None
    actor_user_id: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class MachineStatusIn(BaseModel):
    machine_id: str
    status: str
    hostname: str | None = None
    os: str | None = None
    username: str | None = None


class MachineSecretVerifyIn(BaseModel):
    machine_id: str
    machine_secret: str


class MachineIdentityOut(BaseModel):
    machine_id: str
    status: str


class InternalControlSessionOut(BaseModel):
    id: str
    machine_id: str
    controller_user_id: int


@router.post("/audit")
async def internal_audit(body: InternalAuditIn, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await record_audit(
        db,
        event_type=body.event_type,
        summary=body.summary,
        actor_type=body.actor_type,
        machine_id=body.machine_id,
        session_id=body.session_id,
        actor_user_id=body.actor_user_id,
        metadata=body.metadata,
    )
    await db.commit()
    return {"status": "ok"}


@router.post("/machines/status")
async def internal_machine_status(body: MachineStatusIn, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    await upsert_machine_status(
        db,
        machine_id=body.machine_id,
        status=body.status,
        hostname=body.hostname,
        os_name=body.os,
        username=body.username,
    )
    await db.commit()
    return {"status": "ok"}


@router.post("/machines/verify-secret", response_model=MachineIdentityOut)
async def internal_verify_machine_secret(body: MachineSecretVerifyIn, db: AsyncSession = Depends(get_db)) -> MachineIdentityOut:
    try:
        machine = await require_valid_machine(db, body.machine_id, body.machine_secret)
    except LookupError:
        await record_audit(
            db,
            event_type="agent_auth_failed",
            summary="Agent machine auth failed: unknown machine",
            actor_type="agent",
            machine_id=body.machine_id or None,
            metadata={"reason": "unknown_machine"},
        )
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid machine credentials")
    except PermissionError as exc:
        reason = str(exc)
        await record_audit(
            db,
            event_type="agent_auth_failed",
            summary=f"Agent machine auth failed: {reason}",
            actor_type="agent",
            machine_id=body.machine_id or None,
            metadata={"reason": reason},
        )
        await db.commit()
        code = status.HTTP_403_FORBIDDEN if reason == "machine_disabled" else status.HTTP_401_UNAUTHORIZED
        raise HTTPException(status_code=code, detail="invalid machine credentials") from exc
    await record_audit(
        db,
        event_type="agent_auth_succeeded",
        summary="Agent machine auth succeeded",
        actor_type="agent",
        machine_id=machine.machine_id,
        metadata={"status": machine.status},
    )
    await db.commit()
    return MachineIdentityOut(machine_id=machine.machine_id, status=machine.status)


@router.get("/control-session/{machine_id}", response_model=InternalControlSessionOut)
async def internal_control_session(machine_id: str, db: AsyncSession = Depends(get_db)) -> InternalControlSessionOut:
    session = await get_active_control_session(db, machine_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="no active control session")
    return InternalControlSessionOut(id=session.id, machine_id=session.machine_id, controller_user_id=session.controller_user_id)


@router.delete("/control-session/{machine_id}")
async def internal_release_control_session(
    machine_id: str,
    controller_user_id: int | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | None]:
    session = await release_active_control_session(db, machine_id, controller_user_id)
    if session is None:
        return {"status": "not_found", "session_id": None}
    await record_audit(
        db,
        event_type="control_released",
        summary="Control released by relay disconnect",
        actor_type="system",
        machine_id=machine_id,
        session_id=session.id,
        actor_user_id=session.controller_user_id,
    )
    await db.commit()
    return {"status": "released", "session_id": session.id}
