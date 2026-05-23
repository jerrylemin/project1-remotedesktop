from __future__ import annotations

import httpx

from apps.relay.config import get_relay_settings


async def post_audit(event: dict) -> None:
    settings = get_relay_settings()
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            await client.post(f"{settings.api_url}/internal/audit", json=event)
    except httpx.HTTPError:
        pass

