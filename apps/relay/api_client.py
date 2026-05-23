from __future__ import annotations

import logging
from typing import Any

import httpx

from apps.relay.config import get_relay_settings

logger = logging.getLogger(__name__)


def internal_headers() -> dict[str, str]:
    return {"X-TelePC-Internal-Secret": get_relay_settings().internal_api_secret}


async def validate_ws_ticket(ws_ticket: str) -> dict[str, Any] | None:
    settings = get_relay_settings()
    try:
        async with httpx.AsyncClient(timeout=3, headers=internal_headers()) as client:
            response = await client.post(f"{settings.api_url}/internal/ws-ticket/validate", json={"ws_ticket": ws_ticket})
            if response.status_code != 200:
                return None
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("ws ticket validation failed: %s", exc)
        return None


async def update_machine_status(machine_id: str, status: str, metadata: dict[str, Any] | None = None) -> None:
    settings = get_relay_settings()
    payload = {"machine_id": machine_id, "status": status}
    payload.update(metadata or {})
    try:
        async with httpx.AsyncClient(timeout=3, headers=internal_headers()) as client:
            response = await client.post(f"{settings.api_url}/internal/machines/status", json=payload)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning("machine status update failed machine=%s status=%s error=%s", machine_id, status, exc)
