from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine, MachineGrant
from apps.api.services.auth import create_user


async def login(api_client, username: str, password: str = "pw") -> str:
    response = await api_client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


async def seed_teacher_and_machine(*, grant_control: bool = False) -> None:
    async with SessionLocal() as db:
        user = await create_user(db, "teacher", "pw", role="teacher")
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.flush()
        if grant_control:
            db.add(MachineGrant(user_id=user.id, machine_id="m1", can_view=True, can_control=True))
        await db.commit()


async def test_teacher_without_machine_grant_cannot_control_machine(api_client) -> None:
    await seed_teacher_and_machine(grant_control=False)
    token = await login(api_client, "teacher")

    response = await api_client.get("/api/machines/m1/processes", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


async def test_teacher_with_machine_grant_can_control_machine(api_client) -> None:
    await seed_teacher_and_machine(grant_control=True)
    token = await login(api_client, "teacher")

    response = await api_client.get("/api/machines/m1/processes", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["command"]["action"] == "list_processes"
