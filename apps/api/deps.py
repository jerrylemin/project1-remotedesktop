from __future__ import annotations

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.config import get_settings
from apps.api.db import get_db
from apps.api.models import MachineGrant, User
from apps.api.security import decode_access_token
from shared.enums import ROLE_PERMISSIONS, Permission


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
    telepc_session: str | None = Cookie(default=None),
) -> User:
    token = telepc_session
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")
    try:
        payload = decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token") from exc
    result = await db.execute(select(User).options(selectinload(User.roles)).where(User.username == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="inactive user")
    return user


def require_permission(permission: Permission):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        role_names = {role.name for role in user.roles}
        permissions = set().union(*(ROLE_PERMISSIONS.get(name, set()) for name in role_names))
        if permission not in permissions:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
        return user

    return dependency


def user_role_names(user: User) -> set[str]:
    return {role.name for role in user.roles}


async def require_machine_access(
    db: AsyncSession,
    user: User,
    machine_id: str,
    action: str,
) -> None:
    roles = user_role_names(user)
    if "admin" in roles:
        return
    if "agent" in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="agent identity cannot use web actions")
    action_field = {
        "view": "can_view",
        "control": "can_control",
        "file": "can_file",
        "webcam": "can_webcam",
        "power": "can_power",
        "audit": "can_audit",
    }.get(action)
    if action_field is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="unknown machine action")
    if "auditor" in roles and action != "audit":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="permission denied")
    grant = await db.scalar(select(MachineGrant).where(MachineGrant.user_id == user.id, MachineGrant.machine_id == machine_id))
    if grant is not None and bool(getattr(grant, action_field)):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="machine grant required")


def cookie_name() -> str:
    return get_settings().cookie_name
