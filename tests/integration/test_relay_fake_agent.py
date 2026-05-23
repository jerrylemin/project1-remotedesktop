from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.security import create_access_token
from apps.relay.main import app
from shared.protocol import make_envelope


def test_fake_agent_frame_forwarded() -> None:
    token = create_access_token("admin", {"uid": 1})
    with TestClient(app) as client:
        with client.websocket_connect("/ws/agent") as agent, client.websocket_connect("/ws/admin") as admin:
            agent.send_json(make_envelope("auth", machine_id="m1", payload={"machine_id": "m1", "machine_secret": "secret"}))
            assert agent.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("auth", payload={"token": token}))
            assert admin.receive_json()["type"] == "ack"
            admin.send_json(make_envelope("subscribe_machine", machine_id="m1", payload={"control": False}))
            assert admin.receive_json()["type"] == "ack"
            agent.send_json(make_envelope("frame", machine_id="m1", payload={"jpeg_b64": "abc"}))
            forwarded = admin.receive_json()
            assert forwarded["type"] == "frame"
            assert forwarded["payload"]["jpeg_b64"] == "abc"
