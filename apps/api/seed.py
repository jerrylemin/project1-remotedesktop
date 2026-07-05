from __future__ import annotations

from apps.api.db import SessionLocal, init_db
from apps.api.models import Machine, MachineSecret, Role, User
from apps.api.services.auth import create_user, ensure_roles
from shared.crypto import hash_secret
from sqlalchemy import select


async def admin_user_exists() -> bool:
    await init_db()
    async with SessionLocal() as db:
        admin_id = await db.scalar(
            select(User.id).join(User.roles).where(Role.name == "admin").limit(1)
        )
        return admin_id is not None


async def seed_admin(username: str, password: str, *, include_demo_machines: bool = False) -> None:
    await init_db()
    async with SessionLocal() as db:
        await ensure_roles(db)
        await create_user(db, username=username, password=password, email="admin@example.local", role="admin")
        if include_demo_machines:
            for machine_id in ("fake-machine-001", "LAB-PC-01", "LAB-PC-02", "HOME-PC-01"):
                existing_fake = await db.scalar(select(Machine).where(Machine.machine_id == machine_id))
                if existing_fake is None:
                    db.add(
                        Machine(
                            machine_id=machine_id,
                            hostname=machine_id,
                            os="FakeOS Demo",
                            username="demo",
                            status="online",
                        )
                    )
                existing_secret = await db.scalar(select(MachineSecret).where(MachineSecret.machine_id == machine_id))
                if existing_secret is None:
                    db.add(MachineSecret(machine_id=machine_id, secret_hash=hash_secret("fake-secret")))
        await db.commit()
