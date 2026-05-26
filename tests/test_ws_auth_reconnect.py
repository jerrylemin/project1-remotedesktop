from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.api.db import SessionLocal
from apps.api.services.auth import create_user
from apps.api.services.ws_ticket import clear_ws_tickets, create_ws_ticket, validate_ws_ticket
from apps.relay.registry import RelayRegistry


async def test_ws_ticket_is_single_use(clean_db) -> None:
    clear_ws_tickets()
    async with SessionLocal() as db:
        user = await create_user(db, "admin", "pw", role="admin")
        await db.commit()
        ticket = create_ws_ticket(user)
    assert validate_ws_ticket(ticket.token) is not None
    assert validate_ws_ticket(ticket.token) is None


def test_registry_stale_offline_transition() -> None:
    registry = RelayRegistry()
    registry.last_heartbeat["m1"] = datetime.now(UTC) - timedelta(seconds=61)
    registry.statuses["m1"] = "online"
    assert registry.stale_or_offline(30, 60) == [("m1", "offline")]
