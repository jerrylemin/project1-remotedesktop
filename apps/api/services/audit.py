from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import AuditEvent
from shared.redaction import redact


async def record_audit(
    db: AsyncSession,
    *,
    event_type: str,
    summary: str,
    actor_type: str = "system",
    machine_id: str | None = None,
    session_id: str | None = None,
    actor_user_id: int | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        summary=summary,
        actor_type=actor_type,
        machine_id=machine_id,
        session_id=session_id,
        actor_user_id=actor_user_id,
        metadata_json=redact(metadata or {}),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(event)
    await db.flush()
    return event


async def list_machine_audit(
    db: AsyncSession,
    machine_id: str,
    limit: int = 100,
    event_type: str | None = None,
    actor_type: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> list[AuditEvent]:
    stmt = select(AuditEvent).where(AuditEvent.machine_id == machine_id)
    if event_type:
        stmt = stmt.where(AuditEvent.event_type == event_type)
    if actor_type:
        stmt = stmt.where(AuditEvent.actor_type == actor_type)
    if start:
        stmt = stmt.where(AuditEvent.created_at >= start)
    if end:
        stmt = stmt.where(AuditEvent.created_at <= end)
    result = await db.execute(stmt.order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit))
    return list(result.scalars().all())


async def list_recent_audit(db: AsyncSession, limit: int = 20) -> list[AuditEvent]:
    result = await db.execute(select(AuditEvent).order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc()).limit(limit))
    return list(result.scalars().all())
