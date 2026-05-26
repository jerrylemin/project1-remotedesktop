from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import require_permission
from apps.api.models import User
from apps.api.schemas import AuditOut
from apps.api.services.audit import list_machine_audit, list_recent_audit
from shared.enums import Permission

router = APIRouter(prefix="/api", tags=["audit"])


@router.get("/machines/{machine_id}/audit", response_model=list[AuditOut])
async def machine_audit(
    machine_id: str,
    event_type: str | None = Query(default=None),
    actor_type: str | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.AUDIT_READ)),
) -> list[AuditOut]:
    return [
        AuditOut(
            id=item.id,
            machine_id=item.machine_id,
            session_id=item.session_id,
            actor_type=item.actor_type,
            event_type=item.event_type,
            summary=item.summary,
            metadata_json=item.metadata_json,
            created_at=item.created_at,
        )
        for item in await list_machine_audit(db, machine_id, event_type=event_type, actor_type=actor_type, start=start, end=end)
    ]


@router.get("/audit", response_model=list[AuditOut])
async def audit_index(
    machine_id: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.AUDIT_READ)),
) -> list[AuditOut]:
    rows = await list_machine_audit(db, machine_id, limit=limit) if machine_id else await list_recent_audit(db, limit=limit)
    return [
        AuditOut(
            id=item.id,
            machine_id=item.machine_id,
            session_id=item.session_id,
            actor_type=item.actor_type,
            event_type=item.event_type,
            summary=item.summary,
            metadata_json=item.metadata_json,
            created_at=item.created_at,
        )
        for item in rows
    ]
