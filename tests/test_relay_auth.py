from __future__ import annotations

from sqlalchemy import select

from apps.api.config import get_settings
from apps.api.db import SessionLocal
from apps.api.models import AuditEvent, Machine, MachineSecret
from shared.crypto import hash_secret


def internal_headers() -> dict[str, str]:
    return {"X-TelePC-Internal-Secret": get_settings().internal_api_secret}


async def seed_machine(machine_id: str = "m1", secret: str = "correct", *, enabled: bool = True) -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id=machine_id, hostname=machine_id, os="Windows", username="student", status="offline", enabled=enabled))
        db.add(MachineSecret(machine_id=machine_id, secret_hash=hash_secret(secret)))
        await db.commit()


async def test_unknown_machine_secret_rejected_and_audited(api_client) -> None:
    response = await api_client.post(
        "/internal/machines/verify-secret",
        headers=internal_headers(),
        json={"machine_id": "missing", "machine_secret": "anything"},
    )

    assert response.status_code == 401
    async with SessionLocal() as db:
        event = await db.scalar(select(AuditEvent).where(AuditEvent.event_type == "agent_auth_failed"))
        assert event is not None
        assert event.machine_id == "missing"
        assert "anything" not in str(event.metadata_json)


async def test_empty_machine_secret_rejected(api_client) -> None:
    await seed_machine()

    response = await api_client.post(
        "/internal/machines/verify-secret",
        headers=internal_headers(),
        json={"machine_id": "m1", "machine_secret": ""},
    )

    assert response.status_code == 401


async def test_wrong_machine_secret_rejected(api_client) -> None:
    await seed_machine()

    response = await api_client.post(
        "/internal/machines/verify-secret",
        headers=internal_headers(),
        json={"machine_id": "m1", "machine_secret": "wrong"},
    )

    assert response.status_code == 401


async def test_correct_machine_secret_accepted_and_marks_online(api_client) -> None:
    await seed_machine()

    response = await api_client.post(
        "/internal/machines/verify-secret",
        headers=internal_headers(),
        json={"machine_id": "m1", "machine_secret": "correct"},
    )

    assert response.status_code == 200
    assert response.json()["machine_id"] == "m1"
    async with SessionLocal() as db:
        machine = await db.scalar(select(Machine).where(Machine.machine_id == "m1"))
        assert machine is not None
        assert machine.status == "online"
        event = await db.scalar(select(AuditEvent).where(AuditEvent.event_type == "agent_auth_succeeded"))
        assert event is not None
        assert "correct" not in str(event.metadata_json)


async def test_disabled_machine_secret_rejected(api_client) -> None:
    await seed_machine(enabled=False)

    response = await api_client.post(
        "/internal/machines/verify-secret",
        headers=internal_headers(),
        json={"machine_id": "m1", "machine_secret": "correct"},
    )

    assert response.status_code == 403
