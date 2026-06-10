from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine


async def test_start_process_rejects_raw_command(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/processes/start",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"process_key": "powershell -EncodedCommand bad"},
    )

    assert response.status_code == 400


async def test_start_process_accepts_allowlisted_key(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/processes/start",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"process_key": "notepad"},
    )

    assert response.status_code == 200
    assert response.json()["command"]["action"] == "start_process"
    assert response.json()["command"]["process_key"] == "notepad"
