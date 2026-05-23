from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps_internal import require_internal_secret
from apps.api.services.audit import record_audit
from apps.api.services.machine import upsert_machine_status

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
