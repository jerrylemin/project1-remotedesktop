from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from apps.relay.config import get_relay_settings

logger = logging.getLogger(__name__)


class RelayAuditBridge:
    def __init__(self) -> None:
        self.queue: asyncio.Queue[dict[str, Any]] | None = None
        self.worker: asyncio.Task | None = None
        self.client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        if self.worker is not None:
            return
        settings = get_relay_settings()
        self.queue = asyncio.Queue(maxsize=500)
        self.client = httpx.AsyncClient(
            timeout=2,
            headers={"X-TelePC-Internal-Secret": settings.internal_api_secret},
        )
        self.worker = asyncio.create_task(self._run(), name="telepc-relay-audit-bridge")

    async def stop(self) -> None:
        if self.worker is not None:
            self.worker.cancel()
            try:
                await self.worker
            except (asyncio.CancelledError, RuntimeError):
                pass
            self.worker = None
        self.queue = None
        if self.client is not None:
            await self.client.aclose()
            self.client = None

    def enqueue(self, event: dict[str, Any]) -> None:
        if self.queue is None:
            logger.warning("relay audit bridge not running; dropping event %s", event.get("event_type"))
            return
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("relay audit queue full; dropping event %s", event.get("event_type"))

    async def _run(self) -> None:
        while True:
            if self.queue is None:
                await asyncio.sleep(0)
                continue
            event = await self.queue.get()
            for attempt in range(3):
                try:
                    await self._post(event)
                    break
                except Exception as exc:
                    logger.warning("relay audit post failed attempt=%s event=%s error=%s", attempt + 1, event.get("event_type"), exc)
                    await asyncio.sleep(0.2 * (attempt + 1))
            self.queue.task_done()

    async def _post(self, event: dict[str, Any]) -> None:
        settings = get_relay_settings()
        client = self.client
        close_client = False
        if client is None:
            client = httpx.AsyncClient(timeout=2, headers={"X-TelePC-Internal-Secret": settings.internal_api_secret})
            close_client = True
        try:
            response = await client.post(f"{settings.api_url}/internal/audit", json=event)
            response.raise_for_status()
        finally:
            if close_client:
                await client.aclose()


audit_bridge = RelayAuditBridge()


async def post_audit(event: dict[str, Any]) -> None:
    await audit_bridge._post(event)
