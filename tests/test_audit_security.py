from __future__ import annotations

import json

from apps.api.db import SessionLocal
from apps.api.services.audit import record_audit


async def test_audit_redacts_all_credential_keys_and_bounds_metadata(clean_db) -> None:
    async with SessionLocal() as db:
        event = await record_audit(
            db,
            event_type="x" * 200,
            summary="s" * 1000,
            metadata={
                "password": "p",
                "token": "t",
                "secret": "s",
                "machine_secret": "m",
                "authorization": "Bearer value",
                "payload": "x" * 20_000,
            },
        )

        encoded = json.dumps(event.metadata_json)
        assert all(value not in encoded for value in ("Bearer value", '"p"', '"t"', '"m"'))
        assert len(encoded) <= 16_384
        assert len(event.event_type) <= 80
        assert len(event.summary) <= 255
