from __future__ import annotations

from datetime import datetime, time, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import require_permission
from apps.api.models import AuditEvent, ControlSession, Machine, User
from apps.api.schemas import AuditOut, DashboardSummaryOut
from apps.api.services.audit import list_recent_audit
from shared.enums import Permission

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def audit_out(item: AuditEvent) -> AuditOut:
    return AuditOut(
        id=item.id,
        machine_id=item.machine_id,
        session_id=item.session_id,
        actor_type=item.actor_type,
        event_type=item.event_type,
        summary=item.summary,
        metadata_json=item.metadata_json,
        created_at=item.created_at,
    )


@router.get("/summary", response_model=DashboardSummaryOut)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.MACHINES_READ)),
) -> DashboardSummaryOut:
    statuses = dict((await db.execute(select(Machine.status, func.count()).group_by(Machine.status))).all())
    active_sessions = await db.scalar(select(func.count()).select_from(ControlSession).where(ControlSession.ended_at.is_(None)))
    today_start = datetime.combine(datetime.now(timezone.utc).date(), time.min, tzinfo=timezone.utc)
    commands_today = await db.scalar(
        select(func.count()).select_from(AuditEvent).where(AuditEvent.created_at >= today_start, AuditEvent.actor_type == "admin")
    )
    stale = int(statuses.get("stale", 0) or 0)
    offline = int(statuses.get("offline", 0) or 0)
    return DashboardSummaryOut(
        online_machines=int(statuses.get("online", 0) or 0),
        stale_machines=stale,
        offline_machines=offline,
        active_sessions=int(active_sessions or 0),
        commands_today=int(commands_today or 0),
        alerts=stale + offline,
    )


@router.get("/recent-audit", response_model=list[AuditOut])
async def dashboard_recent_audit(
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(Permission.AUDIT_READ)),
) -> list[AuditOut]:
    return [audit_out(item) for item in await list_recent_audit(db, limit=limit)]
