from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import ConsentDecision, ConsentRequest
from apps.api.services.audit import record_audit
from shared.time_utils import utc_now

SENSITIVE_COMMANDS = {
    "SCREENSHOT",
    "LIVE_SCREEN",
    "KEY_INPUT",
    "KEYLOGGER_START",
    "FILE_DOWNLOAD",
    "WEBCAM_START",
    "POWER_RESTART",
    "POWER_SHUTDOWN",
}


def as_aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


async def create_consent_request(
    db: AsyncSession,
    *,
    machine_id: str,
    command_type: str,
    requested_by: str,
    reason: str,
    ttl_seconds: int,
    command_id: str | None = None,
) -> ConsentRequest:
    command_type = command_type.upper()
    request = ConsentRequest(
        id=str(uuid4()),
        command_id=command_id,
        machine_id=machine_id,
        requested_by=str(requested_by),
        command_type=command_type,
        status="pending",
        reason=reason,
        expires_at=utc_now() + timedelta(seconds=max(1, ttl_seconds)),
    )
    db.add(request)
    await record_audit(
        db,
        event_type="consent_requested",
        summary=f"Consent requested for {command_type}",
        actor_type="admin",
        actor_user_id=int(requested_by) if str(requested_by).isdigit() else None,
        machine_id=machine_id,
        metadata={"consent_id": request.id, "command_type": command_type, "reason": reason},
    )
    await db.flush()
    return request


async def record_consent_decision(db: AsyncSession, consent_id: str, decision: str, decided_by: str) -> ConsentRequest:
    decision = decision.lower()
    if decision not in {"approved", "denied"}:
        raise ValueError("decision must be approved or denied")
    request = await db.scalar(select(ConsentRequest).where(ConsentRequest.id == consent_id))
    if request is None:
        raise LookupError("consent request not found")
    if as_aware_utc(request.expires_at) <= utc_now() and request.status == "pending":
        request.status = "expired"
    elif request.status == "pending":
        request.status = decision
        request.decided_by = decided_by
        request.decided_at = utc_now()
        db.add(ConsentDecision(consent_id=consent_id, decision=decision, decided_by=decided_by))
    await record_audit(
        db,
        event_type=f"consent_{request.status}",
        summary=f"Consent {request.status} for {request.command_type}",
        actor_type="agent",
        machine_id=request.machine_id,
        metadata={"consent_id": request.id, "command_type": request.command_type, "decided_by": decided_by},
    )
    await db.flush()
    return request


async def require_active_consent(db: AsyncSession, machine_id: str, command_type: str, requested_by: str) -> ConsentRequest:
    command_type = command_type.upper()
    request = await db.scalar(
        select(ConsentRequest)
        .where(
            ConsentRequest.machine_id == machine_id,
            ConsentRequest.command_type == command_type,
            ConsentRequest.requested_by == str(requested_by),
        )
        .order_by(ConsentRequest.created_at.desc())
    )
    if request is None:
        await record_audit(
            db,
            event_type="consent_missing",
            summary=f"Consent required for {command_type}",
            actor_type="system",
            machine_id=machine_id,
            actor_user_id=int(requested_by) if str(requested_by).isdigit() else None,
            metadata={"command_type": command_type},
        )
        raise PermissionError("consent_required")
    if as_aware_utc(request.expires_at) <= utc_now():
        request.status = "expired"
        await record_audit(
            db,
            event_type="consent_expired",
            summary=f"Consent expired for {command_type}",
            actor_type="system",
            machine_id=machine_id,
            metadata={"consent_id": request.id, "command_type": command_type},
        )
        await db.flush()
        raise PermissionError("consent_expired")
    if request.status != "approved":
        await record_audit(
            db,
            event_type="consent_blocked",
            summary=f"Consent {request.status} blocks {command_type}",
            actor_type="system",
            machine_id=machine_id,
            metadata={"consent_id": request.id, "command_type": command_type, "status": request.status},
        )
        raise PermissionError("consent_not_approved")
    return request
