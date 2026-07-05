from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import ConsentDecision, ConsentRequest
from apps.api.services.audit import record_audit
from shared.time_utils import utc_now

SENSITIVE_COMMANDS = {
    "APPLICATION_START",
    "APPLICATION_STOP",
    "PROCESS_KILL",
    "SCREENSHOT",
    "LIVE_SCREEN",
    "LIVE_SCREEN_START",
    "LIVE_SCREEN_STOP",
    "KEY_INPUT",
    "KEYLOGGER_START",
    "KEYLOGGER_STOP",
    "KEYLOGGER_EXPORT",
    "FILE_LIST",
    "FILE_DOWNLOAD",
    "WEBCAM_ENUMERATE",
    "WEBCAM_START",
    "WEBCAM_STOP",
    "POWER_RESTART",
    "POWER_SHUTDOWN",
}


def as_aware_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def canonicalize_command_payload(payload: dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def compute_command_payload_hash(action_type: str, machine_id: str, requested_by: str, payload: dict[str, Any] | None) -> str:
    body = {
        "action_type": action_type.upper(),
        "machine_id": machine_id,
        "requested_by": str(requested_by),
        "payload": json.loads(canonicalize_command_payload(payload)),
    }
    return hashlib.sha256(canonicalize_command_payload(body).encode("utf-8")).hexdigest()


async def create_consent_request(
    db: AsyncSession,
    *,
    machine_id: str,
    command_type: str,
    requested_by: str,
    reason: str,
    ttl_seconds: int,
    command_id: str | None = None,
    command_payload: dict[str, Any] | None = None,
) -> ConsentRequest:
    command_type = command_type.upper()
    payload_hash = compute_command_payload_hash(command_type, machine_id, requested_by, command_payload)
    request = ConsentRequest(
        id=str(uuid4()),
        command_id=command_id or str(uuid4()),
        payload_hash=payload_hash,
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
        metadata={"consent_id": request.id, "command_id": request.command_id, "command_type": command_type, "payload_hash": payload_hash, "reason": reason},
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
        metadata={"consent_id": request.id, "command_id": request.command_id, "command_type": request.command_type, "payload_hash": request.payload_hash, "decided_by": decided_by},
    )
    await db.flush()
    return request


async def require_active_consent(
    db: AsyncSession,
    machine_id: str,
    command_type: str,
    requested_by: str,
    command_payload: dict[str, Any] | None = None,
    command_id: str | None = None,
) -> ConsentRequest:
    command_type = command_type.upper()
    payload_hash = compute_command_payload_hash(command_type, machine_id, requested_by, command_payload)
    conditions = [
            ConsentRequest.machine_id == machine_id,
            ConsentRequest.command_type == command_type,
            ConsentRequest.requested_by == str(requested_by),
            ConsentRequest.payload_hash == payload_hash,
    ]
    if command_id is not None:
        conditions.append(ConsentRequest.command_id == command_id)
    request = await db.scalar(
        select(ConsentRequest)
        .where(*conditions)
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
            metadata={"command_type": command_type, "payload_hash": payload_hash},
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
            metadata={"consent_id": request.id, "command_type": command_type, "payload_hash": payload_hash},
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
            metadata={"consent_id": request.id, "command_type": command_type, "payload_hash": payload_hash, "status": request.status},
        )
        raise PermissionError("consent_not_approved")
    return request


async def consume_active_consent(
    db: AsyncSession,
    machine_id: str,
    command_type: str,
    requested_by: str,
    command_payload: dict[str, Any] | None = None,
    command_id: str | None = None,
) -> ConsentRequest:
    request = await require_active_consent(db, machine_id, command_type, requested_by, command_payload, command_id)
    request.status = "consumed"
    await record_audit(
        db,
        event_type="consent_consumed",
        summary=f"Consent consumed for {command_type.upper()}",
        actor_type="system",
        machine_id=machine_id,
        actor_user_id=int(requested_by) if str(requested_by).isdigit() else None,
        metadata={"consent_id": request.id, "command_id": request.command_id, "command_type": command_type.upper(), "payload_hash": request.payload_hash},
    )
    await db.flush()
    return request
