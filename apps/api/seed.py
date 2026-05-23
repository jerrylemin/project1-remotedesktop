from __future__ import annotations

from apps.api.db import SessionLocal, init_db
from apps.api.models import Machine
from apps.api.services.auth import create_user, ensure_roles
from sqlalchemy import select


async def seed_admin(username: str = "admin", password: str = "admin123") -> None:
    await init_db()
    async with SessionLocal() as db:
        await ensure_roles(db)
        await create_user(db, username=username, password=password, email="admin@example.local", role="admin")
        existing_fake = await db.scalar(select(Machine).where(Machine.machine_id == "fake-machine-001"))
        if existing_fake is None:
            db.add(
                Machine(
                    machine_id="fake-machine-001",
                    hostname="telepc-fake-agent",
                    os="FakeOS Demo",
                    username="demo",
                    status="online",
                )
            )
        await db.commit()
