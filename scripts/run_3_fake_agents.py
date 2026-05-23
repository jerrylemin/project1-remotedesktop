from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.agent.fake_agent import run_fake_agent


MACHINES = ["LAB-PC-01", "LAB-PC-02", "HOME-PC-01"]


async def main_async() -> None:
    await asyncio.gather(*(run_fake_agent(machine_id) for machine_id in MACHINES))


if __name__ == "__main__":
    asyncio.run(main_async())
