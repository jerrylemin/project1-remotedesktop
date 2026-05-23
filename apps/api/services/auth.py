from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.models import Role, User
from apps.api.security import create_access_token, hash_password, verify_password
from shared.enums import ROLE_PERMISSIONS


async def ensure_roles(db: AsyncSession) -> None:
    for role_name, permissions in ROLE_PERMISSIONS.items():
        existing = await db.scalar(select(Role).where(Role.name == role_name))
        if existing is None:
            db.add(Role(name=role_name, permissions_json=[permission.value for permission in permissions]))
    await db.flush()


async def create_user(db: AsyncSession, username: str, password: str, email: str | None = None, role: str = "admin") -> User:
    await ensure_roles(db)
    existing = await db.scalar(select(User).where(User.username == username))
    if existing:
        return existing
    role_obj = await db.scalar(select(Role).where(Role.name == role))
    user = User(username=username, email=email, password_hash=hash_password(password), roles=[role_obj] if role_obj else [])
    db.add(user)
    await db.flush()
    return user


async def authenticate(db: AsyncSession, username: str, password: str) -> tuple[User, str] | None:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return None
    return user, create_access_token(user.username, {"uid": user.id})

