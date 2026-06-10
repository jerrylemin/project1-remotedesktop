from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.consent import create_consent_request, record_consent_decision


async def test_start_application_rejects_non_whitelisted_app(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/applications/start",
        headers=headers,
        json={"name": "cmd", "command": "cmd.exe"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "application not in whitelist"


async def test_start_whitelisted_application_requires_consent(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.post("/api/machines/m1/applications/start", headers=headers, json={"name": "chrome"})

    assert response.status_code == 403
    assert "consent" in response.json()["detail"]


async def test_start_whitelisted_application_ignores_raw_command(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="APPLICATION_START",
            requested_by="1",
            reason="start chrome",
            ttl_seconds=60,
        )
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/applications/start",
        headers=headers,
        json={"name": "chrome", "command": "powershell -EncodedCommand bad"},
    )

    assert response.status_code == 200
    assert response.json()["command"] == {"action": "start_application", "app_key": "chrome", "name": "chrome", "confirm": False}
