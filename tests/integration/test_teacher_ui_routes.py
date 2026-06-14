from __future__ import annotations

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.audit import record_audit
from apps.api.services.consent import create_consent_request, record_consent_decision


async def test_admin_pages_render(api_client, admin_token: str) -> None:
    api_client.cookies.set("telepc_session", admin_token)
    for path in ["/admin/dashboard", "/admin/machines", "/admin/machines/m1", "/admin/audit"]:
        response = await api_client.get(path)
        assert response.status_code == 200
        assert "TelePC" in response.text or "Remote Shell" in response.text


async def test_dashboard_summary_and_recent_audit(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        db.add(Machine(machine_id="m2", hostname="pc2", os="Windows", username="student", status="offline"))
        await record_audit(db, event_type="processes_listed", summary="listed", actor_type="admin", machine_id="m1")
        await db.commit()

    summary = await api_client.get("/api/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["online_machines"] == 1
    assert summary.json()["offline_machines"] == 1
    assert summary.json()["commands_today"] >= 1

    recent = await api_client.get("/api/dashboard/recent-audit", headers=headers)
    assert recent.status_code == 200
    assert recent.json()[0]["event_type"] == "processes_listed"


async def test_machine_audit_api_filters_to_machine(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        await record_audit(db, event_type="agent_online", summary="m1 only", machine_id="m1")
        await record_audit(db, event_type="agent_online", summary="m2 only", machine_id="m2")
        await db.commit()
    response = await api_client.get("/api/machines/m1/audit", headers=headers)
    assert response.status_code == 200
    assert [row["summary"] for row in response.json()] == ["m1 only"]


async def test_protected_process_stop_is_denied_and_audited(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    response = await api_client.post("/api/machines/m1/processes/500/stop", headers=headers, json={"name": "lsass.exe", "confirm": True})
    assert response.status_code == 403

    audit = await api_client.get("/api/machines/m1/audit?event_type=acl_denied", headers=headers)
    assert audit.status_code == 200
    assert audit.json()[0]["summary"].startswith("Protected process stop denied")


async def test_process_stop_requires_approved_consent(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    blocked = await api_client.post("/api/machines/m1/processes/500/stop", headers=headers, json={"name": "notepad.exe", "confirm": True})
    assert blocked.status_code == 403
    assert "consent" in blocked.json()["detail"]

    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="PROCESS_KILL",
            requested_by="1",
            reason="stop notepad",
            ttl_seconds=60,
        )
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    accepted = await api_client.post("/api/machines/m1/processes/500/stop", headers=headers, json={"name": "notepad.exe", "confirm": True})
    assert accepted.status_code == 200
    assert accepted.json()["command"]["action"] == "stop_process"


async def test_power_requires_confirm_and_reason(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()

    missing_reason = await api_client.post("/api/machines/m1/power", headers=headers, json={"action": "restart", "confirm": True, "reason": ""})
    assert missing_reason.status_code == 400

    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="POWER_RESTART",
            requested_by="1",
            reason="demo restart",
            ttl_seconds=60,
        )
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    accepted = await api_client.post("/api/machines/m1/power", headers=headers, json={"action": "restart", "confirm": True, "reason": "demo restart"})
    assert accepted.status_code == 200
    assert accepted.json()["command"]["power_action"] == "restart"

    missing_confirm = await api_client.post("/api/machines/m1/power", headers=headers, json={"action": "lock"})
    assert missing_confirm.status_code == 400

    lock = await api_client.post("/api/machines/m1/power", headers=headers, json={"action": "lock", "confirm": True})
    assert lock.status_code == 200
    assert lock.json()["command"]["power_action"] == "lock"
    assert lock.json()["command"]["reason"] == "lock workstation"

    cancel = await api_client.post("/api/machines/m1/power", headers=headers, json={"action": "cancel", "confirm": True})
    assert cancel.status_code == 200
    assert cancel.json()["command"]["power_action"] == "cancel"


async def test_sandbox_alias_routes(api_client, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()
    files = await api_client.get("/api/machines/m1/sandbox/files", headers=headers)
    jobs = await api_client.get("/api/machines/m1/sandbox/jobs", headers=headers)
    assert files.status_code == 200
    assert jobs.status_code == 200
