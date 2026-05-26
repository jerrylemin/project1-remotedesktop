from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.auth import create_user
from apps.relay.main import app as relay_app
from shared.protocol import make_envelope


async def test_second_admin_claim_is_rejected(api_client) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await create_user(db, "a1", "pw", role="admin")
        await create_user(db, "a2", "pw", role="admin")
        await db.commit()
    t1 = (await api_client.post("/auth/login", json={"username": "a1", "password": "pw"})).json()["access_token"]
    t2 = (await api_client.post("/auth/login", json={"username": "a2", "password": "pw"})).json()["access_token"]
    assert (await api_client.post("/api/sessions", headers={"Authorization": f"Bearer {t1}"}, json={"machine_id": "m1"})).status_code == 200
    assert (await api_client.post("/api/sessions", headers={"Authorization": f"Bearer {t2}"}, json={"machine_id": "m1"})).status_code == 409


def test_observer_command_rejected_with_observer_only(monkeypatch) -> None:
    async def fake_validate(ticket: str):
        return {"user_id": 1, "username": "admin", "can_control": True, "permissions": ["machines:control"]}

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    with TestClient(relay_app) as client, client.websocket_connect("/ws/admin") as admin:
        admin.send_json(make_envelope("auth", payload={"ws_ticket": "ticket"}))
        assert admin.receive_json()["type"] == "ack"
        admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": False}))
        assert admin.receive_json()["type"] == "ack"
        admin.send_json(make_envelope("command", machine_id="m1", payload={"action": "stop_process", "pid": 1}))
        response = admin.receive_json()
        assert response["type"] == "error"
        assert response["payload"]["detail"] == "observer_only"
