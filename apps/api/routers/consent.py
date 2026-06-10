from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import require_machine_access, require_permission
from apps.api.models import User
from apps.api.schemas import ConsentDecisionIn, ConsentRequestIn, ConsentRequestOut
from apps.api.services.consent import create_consent_request, record_consent_decision
from apps.api.services.machine import get_machine
from shared.enums import Permission

router = APIRouter(prefix="/api", tags=["consent"])


def consent_out(request) -> ConsentRequestOut:
    return ConsentRequestOut(
        id=request.id,
        command_id=request.command_id,
        machine_id=request.machine_id,
        requested_by=request.requested_by,
        command_type=request.command_type,
        status=request.status,
        reason=request.reason,
        expires_at=request.expires_at,
        decided_by=request.decided_by,
        decided_at=request.decided_at,
        created_at=request.created_at,
    )


@router.post("/machines/{machine_id}/consent-requests", response_model=ConsentRequestOut)
async def request_machine_consent(
    machine_id: str,
    body: ConsentRequestIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> ConsentRequestOut:
    if await get_machine(db, machine_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="machine not found")
    await require_machine_access(db, user, machine_id, "control")
    request = await create_consent_request(
        db,
        machine_id=machine_id,
        command_type=body.command_type,
        requested_by=str(user.id),
        reason=body.reason,
        ttl_seconds=body.ttl_seconds,
    )
    await db.commit()
    return consent_out(request)


@router.post("/consent-requests/{consent_id}/decision", response_model=ConsentRequestOut)
async def decide_machine_consent(
    consent_id: str,
    body: ConsentDecisionIn,
    db: AsyncSession = Depends(get_db),
) -> ConsentRequestOut:
    try:
        request = await record_consent_decision(db, consent_id, body.decision, body.decided_by)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="consent request not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await db.commit()
    return consent_out(request)
