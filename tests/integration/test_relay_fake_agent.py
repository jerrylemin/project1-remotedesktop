from __future__ import annotations

from fastapi.testclient import TestClient

from apps.relay.main import app
from shared.protocol import make_envelope


def test_fake_agent_frame_forwarded(monkeypatch) -> None:
    async def fake_validate(ticket: str):
        return {"user_id": 1, "username": "admin", "can_control": True, "permissions": ["machines:control"]}

    async def noop_status(*args, **kwargs):
        return None

    async def accept_agent(machine_id: str, machine_secret: str) -> bool:
        return True

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    monkeypatch.setattr("apps.relay.router.update_machine_status", noop_status)
    monkeypatch.setattr("apps.relay.router.validate_agent_secret", accept_agent)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/agent") as agent, client.websocket_connect("/ws/admin") as admin:
            agent.send_json(make_envelope("auth", machine_id="m1", payload={"machine_id": "m1", "machine_secret": "secret"}))
            assert agent.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("auth", payload={"ws_ticket": "ticket"}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": False}))
            assert admin.receive_json()["type"] == "ack"
            agent.send_json(make_envelope("frame", machine_id="m1", payload={"jpeg_b64": "abc"}))
            forwarded = admin.receive_json()
            assert forwarded["type"] == "frame"
            assert forwarded["payload"]["jpeg_b64"] == "abc"


def test_agent_consent_decision_is_recorded_before_forwarding(monkeypatch) -> None:
    recorded = []

    async def fake_validate(ticket: str):
        return {"user_id": 1, "username": "admin", "can_control": True, "permissions": ["machines:control"]}

    async def noop_status(*args, **kwargs):
        return None

    async def accept_agent(machine_id: str, machine_secret: str) -> bool:
        return True

    async def record(machine_id: str, consent_id: str, decision: str) -> bool:
        recorded.append((machine_id, consent_id, decision))
        return True

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    monkeypatch.setattr("apps.relay.router.update_machine_status", noop_status)
    monkeypatch.setattr("apps.relay.router.validate_agent_secret", accept_agent)
    monkeypatch.setattr("apps.relay.router.record_agent_consent_decision", record)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/agent") as agent, client.websocket_connect("/ws/admin") as admin:
            agent.send_json(make_envelope("auth", machine_id="m1", payload={"machine_id": "m1", "machine_secret": "secret"}))
            assert agent.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("auth", payload={"ws_ticket": "ticket"}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": False}))
            assert admin.receive_json()["type"] == "ack"
            agent.send_json(make_envelope("command_result", machine_id="m1", payload={"ok": True, "result": {"consent_id": "c1", "decision": "approved"}}))
            forwarded = admin.receive_json()

    assert forwarded["payload"]["result"]["decision"] == "approved"
    assert recorded == [("m1", "c1", "approved")]
