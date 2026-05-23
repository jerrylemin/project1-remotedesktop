from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from apps.relay.api_client import update_machine_status
from apps.relay.audit_bridge import audit_bridge
from apps.relay.config import get_relay_settings
from apps.relay.registry import registry
from apps.relay.router import router


async def status_monitor() -> None:
    settings = get_relay_settings()
    while True:
        await asyncio.sleep(max(1, settings.heartbeat_timeout_seconds))
        for machine_id, status in registry.stale_or_offline(settings.heartbeat_timeout_seconds, settings.offline_timeout_seconds):
            await update_machine_status(machine_id, status)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await audit_bridge.start()
    monitor = asyncio.create_task(status_monitor(), name="telepc-relay-status-monitor")
    try:
        yield
    finally:
        monitor.cancel()
        try:
            await monitor
        except asyncio.CancelledError:
            pass
        await audit_bridge.stop()


def create_app() -> FastAPI:
    app = FastAPI(title="TelePC Relay", version="0.1.0", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()
