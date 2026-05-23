from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.services.audit import record_audit


async def test_audit_machine_filter(api_client, admin_token: str) -> None:
    async with SessionLocal() as db:
        await record_audit(db, event_type="agent_online", summary="online", actor_type="agent", machine_id="m1")
        await record_audit(db, event_type="control_claimed", summary="claimed", actor_type="admin", machine_id="m1")
        await record_audit(db, event_type="agent_online", summary="other", actor_type="agent", machine_id="m2")
        await db.commit()
    response = await api_client.get(
        "/api/machines/m1/audit",
        params={"event_type": "agent_online", "actor_type": "agent"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["summary"] == "online"

