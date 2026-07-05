from __future__ import annotations

import pytest

from apps.api.db import SessionLocal
from apps.api.models import Machine
from apps.api.services.consent import (
    compute_command_payload_hash,
    create_consent_request,
    record_consent_decision,
    require_active_consent,
)


async def seed_machine() -> None:
    async with SessionLocal() as db:
        db.add(Machine(machine_id="m1", hostname="pc1", os="Windows", username="student", status="online"))
        await db.commit()


async def approve(command_type: str, payload: dict) -> None:
    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type=command_type,
            requested_by="1",
            reason="test",
            ttl_seconds=60,
            command_id="cmd-1",
            command_payload=payload,
        )
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()


async def test_approved_chrome_start_cannot_start_notepad(clean_db) -> None:
    await seed_machine()
    await approve("APPLICATION_START", {"name": "chrome", "confirm": True})

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, "m1", "APPLICATION_START", "1", {"name": "notepad", "confirm": True})


async def test_approved_file_list_root_cannot_list_other_root(clean_db) -> None:
    await seed_machine()
    await approve("FILE_LIST", {"root_path": "C:\\Remote", "relative_path": "", "consent": True})

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, "m1", "FILE_LIST", "1", {"root_path": "D:\\Remote", "relative_path": "", "consent": True})


async def test_approved_file_download_path_cannot_download_other_path(clean_db) -> None:
    await seed_machine()
    await approve("FILE_DOWNLOAD", {"root_path": "C:\\Remote", "relative_path": "a.txt", "consent": True})

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, "m1", "FILE_DOWNLOAD", "1", {"root_path": "C:\\Remote", "relative_path": "b.txt", "consent": True})


async def test_approved_webcam_device_zero_cannot_start_device_one(clean_db) -> None:
    await seed_machine()
    await approve("WEBCAM_START", {"consent": True, "device_id": "camera-0"})

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, "m1", "WEBCAM_START", "1", {"consent": True, "device_id": "camera-1"})


async def test_approved_process_pid_cannot_kill_other_pid(clean_db) -> None:
    await seed_machine()
    await approve("PROCESS_KILL", {"pid": 123, "name": "notepad.exe", "confirm": True})

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, "m1", "PROCESS_KILL", "1", {"pid": 456, "name": "notepad.exe", "confirm": True})


def test_payload_hash_distinguishes_secret_values() -> None:
    assert compute_command_payload_hash("FILE_DOWNLOAD", "m1", "1", {"token": "a"}) != compute_command_payload_hash(
        "FILE_DOWNLOAD", "m1", "1", {"token": "b"}
    )


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ({"name": "chrome"}, {"name": "notepad"}),
        ({"pid": 1}, {"pid": 2}),
        ({"root_path": "C:\\Remote"}, {"root_path": "D:\\Remote"}),
        ({"relative_path": "a.txt"}, {"relative_path": "b.txt"}),
        ({"device_id": "camera-0"}, {"device_id": "camera-1"}),
        ({"ttl_seconds": 30}, {"ttl_seconds": 60}),
        ({"pid": 1}, {"pid": "1"}),
        ({"name": "é"}, {"name": "e\u0301"}),
        ({"name": "chrome"}, {"name": "chrome", "extra": True}),
    ],
)
def test_consent_fuzz_rejects_every_payload_difference(left: dict, right: dict) -> None:
    assert compute_command_payload_hash("ACTION", "m1", "1", left) != compute_command_payload_hash("ACTION", "m1", "1", right)


def test_consent_hash_is_stable_for_reordered_json_but_not_other_identity() -> None:
    left = compute_command_payload_hash("ACTION", "m1", "1", {"a": 1, "b": 2})
    assert left == compute_command_payload_hash("ACTION", "m1", "1", {"b": 2, "a": 1})
    assert left != compute_command_payload_hash("ACTION", "m2", "1", {"a": 1, "b": 2})
    assert left != compute_command_payload_hash("ACTION", "m1", "2", {"a": 1, "b": 2})


async def test_approved_consent_cannot_authorize_different_command_id(clean_db) -> None:
    await seed_machine()
    payload = {"name": "chrome", "confirm": True}
    async with SessionLocal() as db:
        consent = await create_consent_request(
            db,
            machine_id="m1",
            command_type="APPLICATION_START",
            requested_by="1",
            reason="test",
            ttl_seconds=60,
            command_id="cmd-1",
            command_payload=payload,
        )
        await record_consent_decision(db, consent.id, "approved", "agent:m1")
        await db.commit()

    async with SessionLocal() as db:
        with pytest.raises(PermissionError, match="consent_required"):
            await require_active_consent(db, "m1", "APPLICATION_START", "1", payload, command_id="cmd-2")
