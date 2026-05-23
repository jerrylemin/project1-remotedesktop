from __future__ import annotations

import asyncio
import json

import websockets

from apps.agent.commands import handle_command
from apps.agent.config import AgentSettings, get_agent_settings
from apps.agent.machine_info import collect_machine_info
from apps.agent.providers import ProviderError, build_providers
from shared.enums import EnvelopeType
from shared.protocol import Envelope, make_envelope


async def run_agent(settings: AgentSettings | None = None) -> None:
    settings = settings or get_agent_settings()
    url = f"{settings.relay_url.rstrip('/')}/ws/agent"
    providers = build_providers(settings.agent_mode)
    async with websockets.connect(url) as ws:
        await ws.send(
            json.dumps(make_envelope(
                EnvelopeType.AUTH,
                machine_id=settings.machine_id,
                payload={
                    "machine_id": settings.machine_id,
                    "machine_secret": settings.machine_token or "fake-secret",
                    "machine_info": collect_machine_info() if settings.agent_mode == "real" else {"hostname": settings.machine_id, "os": "FakeOS Demo", "username": "demo"},
                },
            ))
        )
        await ws.recv()
        frame_task = asyncio.create_task(send_frames(ws, settings, providers))
        heartbeat_task = asyncio.create_task(send_heartbeats(ws, settings))
        try:
            async for raw in ws:
                envelope = Envelope.model_validate_json(raw)
                if envelope.type == EnvelopeType.COMMAND:
                    try:
                        result = await handle_command(settings.machine_id, envelope.payload, settings.sandbox_root, providers)
                        payload = {"ok": True, "result": result}
                    except ProviderError as exc:
                        payload = {"ok": False, "error": str(exc), "event_type": "command_failed"}
                    except Exception as exc:
                        payload = {"ok": False, "error": str(exc), "event_type": "command_failed"}
                    await ws.send(json.dumps(make_envelope(EnvelopeType.COMMAND_RESULT, machine_id=settings.machine_id, session_id=envelope.session_id, payload=payload)))
        finally:
            frame_task.cancel()
            heartbeat_task.cancel()


async def send_frames(ws, settings: AgentSettings, providers) -> None:
    while True:
        try:
            frame = providers.screen.capture_jpeg_b64()
            payload = {"jpeg_b64": frame, "fps": 1}
        except ProviderError as exc:
            payload = {"error": str(exc), "event_type": "command_failed"}
        await ws.send(json.dumps(make_envelope(EnvelopeType.FRAME, machine_id=settings.machine_id, payload=payload)))
        await asyncio.sleep(1)


async def send_heartbeats(ws, settings: AgentSettings) -> None:
    while True:
        await ws.send(json.dumps(make_envelope(EnvelopeType.HEARTBEAT, machine_id=settings.machine_id, payload={"mode": settings.agent_mode})))
        await asyncio.sleep(5)
