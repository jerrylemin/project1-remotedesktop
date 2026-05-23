from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine


async def test_machine_list(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()
    response = await api_client.get("/api/machines", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()[0]["machine_id"] == "m1"

