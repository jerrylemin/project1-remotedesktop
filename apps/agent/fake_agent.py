from __future__ import annotations

import asyncio

from apps.agent.config import AgentSettings, get_agent_settings
from apps.agent.consent import require_consent_banner
from apps.agent.ws_client import run_agent


async def run_fake_agent(machine_id: str | None = None) -> None:
    base = get_agent_settings()
    settings = AgentSettings(
        relay_url=base.relay_url,
        api_url=base.api_url,
        machine_token=base.machine_token or "fake-secret",
        machine_id=machine_id or base.machine_id,
        sandbox_root=base.sandbox_root,
        require_consent=base.require_consent,
        agent_mode="fake",
    )
    require_consent_banner(settings.machine_id, real_mode=False)
    await run_agent(settings)


def main() -> None:
    settings = get_agent_settings()
    settings.agent_mode = "fake"
    require_consent_banner(settings.machine_id, real_mode=False)
    asyncio.run(run_agent(settings))


if __name__ == "__main__":
    main()
