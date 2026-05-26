from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import ControlSession, SessionParticipant
from shared.time_utils import utc_now


async def create_control_session(db: AsyncSession, machine_id: str, controller_user_id: int) -> ControlSession:
    active = await db.scalar(
        select(ControlSession).where(
            ControlSession.machine_id == machine_id,
            ControlSession.ended_at.is_(None),
        )
    )
    if active:
        if active.controller_user_id == controller_user_id:
            return active
        raise ValueError("machine already controlled")
    session = ControlSession(id=str(uuid4()), machine_id=machine_id, controller_user_id=controller_user_id)
    db.add(session)
    db.add(SessionParticipant(session_id=session.id, user_id=controller_user_id, role="controller"))
    await db.flush()
    return session


async def get_active_control_session(db: AsyncSession, machine_id: str) -> ControlSession | None:
    return await db.scalar(
        select(ControlSession).where(
            ControlSession.machine_id == machine_id,
            ControlSession.ended_at.is_(None),
        )
    )


async def release_control_session(db: AsyncSession, session_id: str) -> ControlSession | None:
    session = await db.scalar(select(ControlSession).where(ControlSession.id == session_id))
    if session and session.ended_at is None:
        session.ended_at = utc_now()
        await db.flush()
    return session


async def release_active_control_session(db: AsyncSession, machine_id: str, controller_user_id: int | None = None) -> ControlSession | None:
    session = await get_active_control_session(db, machine_id)
    if session is None:
        return None
    if controller_user_id is not None and session.controller_user_id != controller_user_id:
        return None
    session.ended_at = utc_now()
    await db.flush()
    return session
