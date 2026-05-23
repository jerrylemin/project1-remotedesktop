from __future__ import annotations

import httpx

from apps.agent.machine_info import collect_machine_info


async def enroll(api_url: str, enroll_token: str) -> dict[str, str]:
    payload = {"enroll_token": enroll_token, **collect_machine_info()}
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(f"{api_url}/api/agents/enroll", json=payload)
        response.raise_for_status()
        return response.json()

