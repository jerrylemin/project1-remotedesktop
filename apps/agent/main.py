from __future__ import annotations

import asyncio

from apps.agent.config import get_agent_settings
from apps.agent.consent import require_consent_banner
from apps.agent.ws_client import run_agent


def main() -> None:
    settings = get_agent_settings()
    require_consent_banner(settings.machine_id, real_mode=settings.agent_mode == "real")
    asyncio.run(run_agent(settings))


if __name__ == "__main__":
    main()
