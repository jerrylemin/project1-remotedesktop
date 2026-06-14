from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.consent import create_consent_request, record_consent_decision


async def test_webcam_start_requires_device_selection(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        consent = await create_consent_request(db, machine_id="m1", command_type="WEBCAM_START", requested_by="1", reason="camera", ttl_seconds=60)
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    response = await api_client.post("/api/machines/m1/webcam/start", headers=headers, json={"consent": True})

    assert response.status_code == 400
    assert response.json()["detail"] == "webcam device_id is required"


async def test_webcam_start_passes_selected_device(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        consent = await create_consent_request(db, machine_id="m1", command_type="WEBCAM_START", requested_by="1", reason="camera", ttl_seconds=60)
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    response = await api_client.post("/api/machines/m1/webcam/start", headers=headers, json={"consent": True, "device_id": "camera-2"})

    assert response.status_code == 200
    assert response.json()["command"]["device_id"] == "camera-2"


async def test_webcam_stop_requires_approved_consent(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    blocked = await api_client.post("/api/machines/m1/webcam/stop", headers=headers, json={"consent": True})
    assert blocked.status_code == 403
    assert "consent" in blocked.json()["detail"]

    async with SessionLocal() as db:
        consent = await create_consent_request(db, machine_id="m1", command_type="WEBCAM_STOP", requested_by="1", reason="stop camera", ttl_seconds=60)
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    accepted = await api_client.post("/api/machines/m1/webcam/stop", headers=headers, json={"consent": True})
    assert accepted.status_code == 200
    assert accepted.json()["command"] == {"action": "webcam", "start": False, "consent": True}
