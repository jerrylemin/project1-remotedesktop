from __future__ import annotations

from fastapi.testclient import TestClient

from apps.relay.main import app
from shared.protocol import make_envelope


def test_ws_without_auth_is_rejected(monkeypatch) -> None:
    async def noop_status(*args, **kwargs):
        return None

    monkeypatch.setattr("apps.relay.router.update_machine_status", noop_status)
    with TestClient(app) as client, client.websocket_connect("/ws/admin") as admin:
        admin.send_json(make_envelope("heartbeat"))
        assert admin.receive_json()["type"] == "error"


def test_expired_ticket_rejected(monkeypatch) -> None:
    async def fake_validate(ticket: str):
        return None

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    with TestClient(app) as client, client.websocket_connect("/ws/admin") as admin:
        admin.send_json(make_envelope("auth", payload={"ws_ticket": "expired"}))
        assert admin.receive_json()["type"] == "error"


def test_user_without_control_permission_rejected_for_control(monkeypatch) -> None:
    async def fake_validate(ticket: str):
        return {"user_id": 2, "username": "auditor", "can_control": False, "permissions": ["machines:read"]}

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    with TestClient(app) as client, client.websocket_connect("/ws/admin") as admin:
        admin.send_json(make_envelope("auth", payload={"ws_ticket": "read-only"}))
        assert admin.receive_json()["type"] == "ack"
        admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": True}))
        response = admin.receive_json()
        assert response["type"] == "error"
        assert response["payload"]["role"] == "control permission denied"


def test_observer_cannot_send_input(monkeypatch) -> None:
    async def fake_validate(ticket: str):
        return {"user_id": 1, "username": "admin", "can_control": True, "permissions": ["machines:control"]}

    async def noop_status(*args, **kwargs):
        return None

    async def accept_agent(machine_id: str, machine_secret: str) -> bool:
        return True

    async def fake_active(machine_id: str):
        return {"id": "s1", "machine_id": machine_id, "controller_user_id": 1}

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    monkeypatch.setattr("apps.relay.router.update_machine_status", noop_status)
    monkeypatch.setattr("apps.relay.router.validate_agent_secret", accept_agent)
    monkeypatch.setattr("apps.relay.api_client.active_control_session", fake_active)
    monkeypatch.setattr("apps.relay.router.active_control_session", fake_active)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/agent") as agent, client.websocket_connect("/ws/admin") as admin:
            agent.send_json(make_envelope("auth", machine_id="m1", payload={"machine_id": "m1", "machine_secret": "secret"}))
            assert agent.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("auth", payload={"ws_ticket": "ticket"}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": False}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("input_event", machine_id="m1", payload={"event": "mouse"}))
            assert admin.receive_json()["type"] == "error"


def test_controller_can_send_command(monkeypatch) -> None:
    async def fake_validate(ticket: str):
        return {"user_id": 1, "username": "admin", "can_control": True, "permissions": ["machines:control"]}

    async def noop_status(*args, **kwargs):
        return None

    async def accept_agent(machine_id: str, machine_secret: str) -> bool:
        return True

    async def fake_active(machine_id: str):
        return {"id": "s1", "machine_id": machine_id, "controller_user_id": 1}

    monkeypatch.setattr("apps.relay.router.validate_ws_ticket", fake_validate)
    monkeypatch.setattr("apps.relay.router.update_machine_status", noop_status)
    monkeypatch.setattr("apps.relay.router.validate_agent_secret", accept_agent)
    monkeypatch.setattr("apps.relay.router.active_control_session", fake_active)
    with TestClient(app) as client:
        with client.websocket_connect("/ws/agent") as agent, client.websocket_connect("/ws/admin") as admin:
            agent.send_json(make_envelope("auth", machine_id="m1", payload={"machine_id": "m1", "machine_secret": "secret"}))
            assert agent.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("auth", payload={"ws_ticket": "ticket"}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": True}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("command", machine_id="m1", payload={"action": "list_processes"}))
            forwarded = agent.receive_json()
            assert forwarded["type"] == "command"
