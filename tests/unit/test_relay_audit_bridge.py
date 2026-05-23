from __future__ import annotations

import asyncio

from apps.relay.audit_bridge import RelayAuditBridge


async def test_relay_audit_bridge_queue_posts_without_blocking(monkeypatch) -> None:
    bridge = RelayAuditBridge()
    posted: list[dict] = []

    async def fake_post(event: dict) -> None:
        posted.append(event)

    monkeypatch.setattr(bridge, "_post", fake_post)
    bridge.queue = asyncio.Queue(maxsize=10)
    bridge.worker = asyncio.create_task(bridge._run())
    bridge.enqueue({"event_type": "machine_selected", "summary": "selected"})
    await asyncio.wait_for(bridge.queue.join(), timeout=2)
    await bridge.stop()
    assert posted == [{"event_type": "machine_selected", "summary": "selected"}]
