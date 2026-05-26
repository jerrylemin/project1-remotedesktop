from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.services.audit import record_audit


async def test_audit_machine_filter_and_redaction(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        await record_audit(db, event_type="application_started", summary="A", actor_type="admin", machine_id="A", metadata={"password": "x"})
        await record_audit(db, event_type="application_started", summary="B", actor_type="admin", machine_id="B")
        await db.commit()
    response = await api_client.get("/api/audit?machine_id=A", headers=headers)
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["machine_id"] == "A"
    assert rows[0]["metadata_json"]["password"] == "[REDACTED]"
