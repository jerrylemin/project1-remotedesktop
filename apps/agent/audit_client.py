from __future__ import annotations

import httpx


async def post_agent_audit(api_url: str, event: dict) -> None:
    try:
        async with httpx.AsyncClient(timeout=2) as client:
            await client.post(f"{api_url}/internal/audit", json=event)
    except httpx.HTTPError:
        pass

