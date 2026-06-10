from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from apps.api.db import SessionLocal
from apps.api.models import AuditEvent, Machine
from apps.api.services.machine import upsert_machine_status
from apps.relay.registry import RelayRegistry


async def test_machine_status_transition_audits_only_on_change(clean_db) -> None:
    async with SessionLocal() as db:
        await upsert_machine_status(db, machine_id="m1", status="online", hostname="pc")
        await upsert_machine_status(db, machine_id="m1", status="online", hostname="pc")
        await upsert_machine_status(db, machine_id="m1", status="stale")
        await upsert_machine_status(db, machine_id="m1", status="offline")
        await db.commit()
        machine = await db.scalar(select(Machine).where(Machine.machine_id == "m1"))
        events = (await db.execute(select(AuditEvent).where(AuditEvent.machine_id == "m1").order_by(AuditEvent.id))).scalars().all()
    assert machine.status == "offline"
    assert [event.event_type for event in events] == ["agent_online", "agent_stale", "agent_offline"]


def test_relay_registry_stale_and_offline_transitions() -> None:
    registry = RelayRegistry()
    registry.last_heartbeat["m1"] = datetime.now(timezone.utc) - timedelta(seconds=20)
    registry.statuses["m1"] = "online"
    assert registry.stale_or_offline(stale_after_seconds=10, offline_after_seconds=30) == [("m1", "stale")]
    registry.last_heartbeat["m1"] = datetime.now(timezone.utc) - timedelta(seconds=40)
    assert registry.stale_or_offline(stale_after_seconds=10, offline_after_seconds=30) == [("m1", "offline")]
