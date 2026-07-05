from __future__ import annotations

import time
from pathlib import Path

import pytest

from apps.agent.key_capture import (
    export_key_capture_events,
    get_key_capture_events,
    record_key_event,
    reset_key_capture_state,
    start_key_capture_session,
    stop_key_capture_session,
)
from apps.api.db import SessionLocal
from apps.api.models import AuditEvent, Machine
from apps.api.services.auth import create_user
from apps.api.services.consent import create_consent_request, record_consent_decision


async def seed_machine() -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()


async def login(api_client, username: str, password: str = "pw") -> str:
    response = await api_client.post("/auth/login", json={"username": username, "password": password})
    return response.json()["access_token"]


async def approve(db, command_type: str, payload: dict) -> None:
    consent = await create_consent_request(
        db,
        machine_id="m1",
        command_type=command_type,
        requested_by="1",
        reason="keylogger lab",
        ttl_seconds=60,
        command_payload=payload,
    )
    await record_consent_decision(db, consent.id, "approved", "agent:m1")


async def test_start_without_auth_rejected(api_client, clean_db) -> None:
    await seed_machine()

    response = await api_client.post("/api/machines/m1/keylogger/start", json={"session_id": "s1", "ttl_seconds": 30, "consent": True})

    assert response.status_code == 401


async def test_start_without_machine_grant_rejected(api_client, clean_db) -> None:
    async with SessionLocal() as db:
        await create_user(db, "teacher", "pw", role="teacher")
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()
    token = await login(api_client, "teacher")

    response = await api_client.post(
        "/api/machines/m1/keylogger/start",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_id": "s1", "ttl_seconds": 30, "consent": True},
    )

    assert response.status_code == 403


async def test_start_without_consent_rejected(api_client, admin_token: str, clean_db) -> None:
    await seed_machine()

    response = await api_client.post(
        "/api/machines/m1/keylogger/start",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"session_id": "s1", "ttl_seconds": 30, "consent": True},
    )

    assert response.status_code == 403


async def test_approved_exact_consent_starts_capture(api_client, admin_token: str, clean_db) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"session_id": "s1", "ttl_seconds": 30, "consent": True}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await approve(db, "KEYLOGGER_START", payload)
        await db.commit()

    response = await api_client.post("/api/machines/m1/keylogger/start", headers=headers, json=payload)

    assert response.status_code == 200
    assert response.json()["command"]["action"] == "keylogger_start"


async def test_approved_other_payload_rejected(api_client, admin_token: str, clean_db) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await approve(db, "KEYLOGGER_START", {"session_id": "s1", "ttl_seconds": 30, "consent": True})
        await db.commit()

    response = await api_client.post(
        "/api/machines/m1/keylogger/start",
        headers=headers,
        json={"session_id": "s2", "ttl_seconds": 30, "consent": True},
    )

    assert response.status_code == 403


def test_mock_key_event_lifecycle_and_redaction() -> None:
    reset_key_capture_state()
    start_key_capture_session(60, {"approved": True}, session_id="s1", machine_id="m1", requested_by="1")

    assert record_key_event("s1", "KeyA", "down", "Notepad")["key_name"] == "KeyA"
    assert record_key_event("s1", "KeyB", "down", "Password Login")["key_name"] == "[REDACTED_SENSITIVE_CONTEXT]"
    assert len(get_key_capture_events("s1")) == 2
    stop_key_capture_session("s1")
    assert record_key_event("s1", "KeyC", "down", "Notepad") is None
    reset_key_capture_state()


def test_ttl_expires_session() -> None:
    reset_key_capture_state()
    start_key_capture_session(1, {"approved": True}, session_id="ttl", machine_id="m1", requested_by="1")
    time.sleep(1.1)

    assert record_key_event("ttl", "KeyA", "down", "Notepad") is None
    reset_key_capture_state()


def test_export_requires_consent() -> None:
    reset_key_capture_state()
    start_key_capture_session(60, {"approved": True}, session_id="s1", machine_id="m1", requested_by="1")
    record_key_event("s1", "KeyA", "down", "Notepad")

    with pytest.raises(PermissionError):
        export_key_capture_events("s1", {"approved": False})
    assert b"KeyA" in export_key_capture_events("s1", {"approved": True})
    reset_key_capture_state()


async def test_keylogger_audit_logs_start(api_client, admin_token: str, clean_db) -> None:
    payload = {"session_id": "s1", "ttl_seconds": 30, "consent": True}
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await approve(db, "KEYLOGGER_START", payload)
        await db.commit()

    await api_client.post("/api/machines/m1/keylogger/start", headers={"Authorization": f"Bearer {admin_token}"}, json=payload)

    async with SessionLocal() as db:
        rows = (await db.execute(AuditEvent.__table__.select().where(AuditEvent.event_type == "keylogger_started"))).all()
    assert rows


def test_keylogger_lab_ui_contract() -> None:
    html = Path("apps/api/templates/machine_detail.html").read_text(encoding="utf-8")
    js = Path("apps/api/static/js/machine_detail.js").read_text(encoding="utf-8")

    assert "Keylogger Lab Module" in html
    assert "keyboard-input" not in html
    assert "/keylogger/start" in js
    assert "apiCommandAwait(`/api/machines/${encodeURIComponent(machineId)}/keylogger/start`" in js
    assert "keyloggerExpiryTimer" in js
    assert "KEYLOGGER_START" in js
    assert "KEYLOGGER_STOP" in js
