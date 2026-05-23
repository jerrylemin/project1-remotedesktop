from __future__ import annotations

import asyncio
import json

import websockets

from apps.agent.commands import handle_command
from apps.agent.config import AgentSettings, get_agent_settings
from apps.agent.screen import fake_jpeg_frame, real_jpeg_frame
from shared.enums import EnvelopeType
from shared.protocol import Envelope, make_envelope


async def run_agent(settings: AgentSettings | None = None) -> None:
    settings = settings or get_agent_settings()
    url = f"{settings.relay_url.rstrip('/')}/ws/agent"
    async with websockets.connect(url) as ws:
        await ws.send(
            json.dumps(make_envelope(
                EnvelopeType.AUTH,
                machine_id=settings.machine_id,
                payload={"machine_id": settings.machine_id, "machine_secret": settings.machine_token or "fake-secret"},
            ))
        )
        await ws.recv()
        frame_task = asyncio.create_task(send_frames(ws, settings))
        try:
            async for raw in ws:
                envelope = Envelope.model_validate_json(raw)
                if envelope.type == EnvelopeType.COMMAND:
                    try:
                        result = await handle_command(settings.machine_id, envelope.payload, settings.sandbox_root)
                        payload = {"ok": True, "result": result}
                    except Exception as exc:
                        payload = {"ok": False, "error": str(exc)}
                    await ws.send(json.dumps(make_envelope(EnvelopeType.COMMAND_RESULT, machine_id=settings.machine_id, session_id=envelope.session_id, payload=payload)))
        finally:
            frame_task.cancel()


async def send_frames(ws, settings: AgentSettings) -> None:
    while True:
        frame = fake_jpeg_frame() if settings.agent_mode == "fake" else real_jpeg_frame()
        await ws.send(json.dumps(make_envelope(EnvelopeType.FRAME, machine_id=settings.machine_id, payload={"jpeg_b64": frame, "fps": 1})))
        await asyncio.sleep(1)
