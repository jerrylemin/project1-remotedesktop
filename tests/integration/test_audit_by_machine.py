from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.services.audit import record_audit


async def test_audit_by_machine_newest_first(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        await record_audit(db, event_type="agent_online", summary="first", machine_id="m1")
        await record_audit(db, event_type="agent_offline", summary="second", machine_id="m1")
        await db.commit()
    response = await api_client.get("/api/machines/m1/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    rows = response.json()
    assert rows[0]["summary"] == "second"

