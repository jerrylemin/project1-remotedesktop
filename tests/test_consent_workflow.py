from __future__ import annotations

import pytest

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.auth import create_user
from apps.api.services.consent import consume_active_consent, create_consent_request, record_consent_decision, require_active_consent


async def seed_user_machine() -> int:
    async with SessionLocal() as db:
        user = await create_user(db, "admin", "pw", role="admin")
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()
        return user.id


async def test_pending_consent_blocks_sensitive_command(clean_db) -> None:
    user_id = await seed_user_machine()
    async with SessionLocal() as db:
        await create_consent_request(db, machine_id="m1", command_type="LIVE_SCREEN", requested_by=str(user_id), reason="class demo", ttl_seconds=60)
        await db.commit()

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_not_approved"):
            await require_active_consent(db, machine_id="m1", command_type="LIVE_SCREEN", requested_by=str(user_id))


async def test_approved_matching_consent_allows_sensitive_command(clean_db) -> None:
    user_id = await seed_user_machine()
    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="LIVE_SCREEN",
            requested_by=str(user_id),
            reason="class demo",
            ttl_seconds=60,
        )
        await record_consent_decision(db, consent.id, "approved", decided_by="agent:m1")
        await db.commit()

    async with SessionLocal() as db:
        active = await require_active_consent(db, machine_id="m1", command_type="LIVE_SCREEN", requested_by=str(user_id))
        assert active.status == "approved"


async def test_approved_different_command_blocks(clean_db) -> None:
    user_id = await seed_user_machine()
    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="WEBCAM_START",
            requested_by=str(user_id),
            reason="camera demo",
            ttl_seconds=60,
        )
        await record_consent_decision(db, consent.id, "approved", decided_by="agent:m1")
        await db.commit()

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, machine_id="m1", command_type="LIVE_SCREEN", requested_by=str(user_id))


async def test_consent_has_command_id_and_is_single_use(clean_db) -> None:
    user_id = await seed_user_machine()
    payload = {"name": "notepad", "confirm": True}
    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="APPLICATION_START",
            requested_by=str(user_id),
            reason="class demo",
            ttl_seconds=60,
            command_payload=payload,
        )
        assert consent.command_id
        await record_consent_decision(db, consent.id, "approved", decided_by="agent:m1")
        await consume_active_consent(db, "m1", "APPLICATION_START", str(user_id), payload)
        await db.commit()

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_not_approved"):
            await consume_active_consent(db, "m1", "APPLICATION_START", str(user_id), payload)
