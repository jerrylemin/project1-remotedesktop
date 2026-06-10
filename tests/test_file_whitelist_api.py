from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.consent import create_consent_request, record_consent_decision


async def test_remote_file_list_requires_consent(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/remote-files/list",
        headers=headers,
        json={"root_path": "C:\\Remote", "relative_path": "", "consent": True},
    )

    assert response.status_code == 403


async def test_remote_file_list_returns_agent_command_after_consent(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        consent = await create_consent_request(db, machine_id="m1", command_type="FILE_LIST", requested_by="1", reason="list remote folder", ttl_seconds=60)
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/remote-files/list",
        headers=headers,
        json={"root_path": "C:\\Remote", "relative_path": "subdir", "consent": True},
    )

    assert response.status_code == 200
    assert response.json()["command"] == {
        "action": "remote_files_list",
        "root_path": "C:\\Remote",
        "relative_path": "subdir",
        "consent": True,
    }
