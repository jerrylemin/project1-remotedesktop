from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.relay.auth import validate_admin_token, validate_agent_secret
from apps.relay.protocol import error_message, parse_message
from apps.relay.registry import registry
from shared.enums import EnvelopeType
from shared.protocol import make_envelope

router = APIRouter()


@router.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    machine_id: str | None = None
    try:
        first = parse_message(await websocket.receive_json())
        if first.type != EnvelopeType.AUTH:
            await websocket.send_json(error_message("first message must be auth"))
            return
        machine_id = first.machine_id or first.payload.get("machine_id")
        machine_secret = first.payload.get("machine_secret", "")
        if not validate_agent_secret(machine_id or "", machine_secret):
            await websocket.send_json(error_message("invalid machine secret", machine_id=machine_id))
            return
        await registry.register_agent(machine_id, websocket)
        await websocket.send_json(make_envelope("ack", machine_id=machine_id, payload={"role": "agent"}))
        while True:
            envelope = parse_message(await websocket.receive_json())
            if envelope.type == EnvelopeType.FRAME:
                for subscriber in registry.subscribers_for(envelope.machine_id or machine_id):
                    await registry.send_json_safe(subscriber, envelope.model_dump(mode="json"))
            elif envelope.type in {EnvelopeType.COMMAND_RESULT, EnvelopeType.JOB_STATUS, EnvelopeType.AUDIT_EVENT}:
                for subscriber in registry.subscribers_for(envelope.machine_id or machine_id):
                    await registry.send_json_safe(subscriber, envelope.model_dump(mode="json"))
            elif envelope.type == EnvelopeType.HEARTBEAT:
                await websocket.send_json(make_envelope("ack", machine_id=machine_id, payload={"heartbeat": "ok"}))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        registry.unregister_agent(websocket)


@router.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        first = parse_message(await websocket.receive_json())
        if first.type != EnvelopeType.AUTH:
            await websocket.send_json(error_message("first message must be auth"))
            return
        token = first.payload.get("token", "")
        try:
            claims = validate_admin_token(token)
        except Exception:
            await websocket.send_json(error_message("invalid admin token"))
            return
        await registry.register_admin(websocket, str(claims.get("uid") or claims.get("sub")))
        await websocket.send_json(make_envelope("ack", payload={"role": "admin"}))
        while True:
            envelope = parse_message(await websocket.receive_json())
            machine_id = envelope.machine_id
            if envelope.type == EnvelopeType.SUBSCRIBE_MACHINE:
                want_control = bool(envelope.payload.get("control", False))
                ok, role = registry.subscribe(websocket, machine_id or "", want_control)
                await websocket.send_json(
                    make_envelope("ack" if ok else "error", machine_id=machine_id, payload={"role": role, "detail": role})
                )
            elif envelope.type in {EnvelopeType.COMMAND, EnvelopeType.INPUT_EVENT, EnvelopeType.FILE_DISPATCH}:
                if not machine_id or not registry.is_controller(websocket, machine_id):
                    await websocket.send_json(error_message("controller lock required", machine_id=machine_id))
                    continue
                agent = registry.agent_for(machine_id)
                if agent is None:
                    await websocket.send_json(error_message("agent offline", machine_id=machine_id))
                    continue
                await agent.send_json(envelope.model_dump(mode="json"))
            elif envelope.type == EnvelopeType.HEARTBEAT:
                await websocket.send_json(make_envelope("ack", payload={"heartbeat": "ok"}))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        registry.unregister_admin(websocket)

