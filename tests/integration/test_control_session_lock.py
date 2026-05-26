from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine


async def test_control_session_lock(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()
    headers = {"Authorization": f"Bearer {admin_token}"}
    first = await api_client.post("/api/sessions", headers=headers, json={"machine_id": "m1"})
    second = await api_client.post("/api/sessions", headers=headers, json={"machine_id": "m1"})
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
