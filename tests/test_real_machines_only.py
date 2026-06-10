from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.seed import seed_admin


async def test_api_machines_hides_seeded_demo_machines(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="fake-machine-001", hostname="fake-machine-001", os="FakeOS Demo", username="demo", status="online"))
        db.add(Machine(machine_id="real-machine-001", hostname="lab-real-01", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.get("/api/machines", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    assert [row["machine_id"] for row in response.json()] == ["real-machine-001"]


async def test_seed_admin_does_not_create_demo_machines_by_default(clean_db) -> None:
    await seed_admin("admin2", "admin123")

    async with SessionLocal() as db:
        machines = await db.execute(Machine.__table__.select())

    assert machines.all() == []
