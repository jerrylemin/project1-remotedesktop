from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.db import get_db
from apps.api.deps import require_permission
from apps.api.models import User
from apps.api.schemas import SessionCreateIn, SessionOut
from apps.api.services.audit import record_audit
from apps.api.services.session import create_control_session, release_control_session
from shared.enums import Permission

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def session_out(session) -> SessionOut:
    return SessionOut(
        id=session.id,
        machine_id=session.machine_id,
        controller_user_id=session.controller_user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )


@router.post("", response_model=SessionOut)
async def create_session(
    body: SessionCreateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> SessionOut:
    try:
        session = await create_control_session(db, body.machine_id, user.id)
    except ValueError as exc:
        await record_audit(db, event_type="control_denied", summary=str(exc), actor_type="admin", actor_user_id=user.id, machine_id=body.machine_id)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    await record_audit(db, event_type="session_created", summary="Control session created", actor_type="admin", actor_user_id=user.id, machine_id=body.machine_id, session_id=session.id)
    await record_audit(db, event_type="control_claimed", summary="Control claimed", actor_type="admin", actor_user_id=user.id, machine_id=body.machine_id, session_id=session.id)
    await db.commit()
    return session_out(session)


@router.post("/{session_id}/claim", response_model=SessionOut)
async def claim_session(session_id: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission(Permission.MACHINES_CONTROL))) -> SessionOut:
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="claim by id is managed by relay lock; create a session instead")


@router.post("/{session_id}/release", response_model=SessionOut)
async def release_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_permission(Permission.MACHINES_CONTROL)),
) -> SessionOut:
    session = await release_control_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")
    await record_audit(db, event_type="control_released", summary="Control released", actor_type="admin", actor_user_id=user.id, machine_id=session.machine_id, session_id=session.id)
    await db.commit()
    return session_out(session)

