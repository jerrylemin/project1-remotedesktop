from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.relay.api_client import active_control_session, release_control_session, update_machine_status, validate_ws_ticket
from apps.relay.audit_bridge import audit_bridge
from apps.relay.auth import validate_agent_secret
from apps.relay.protocol import error_message, parse_message
from apps.relay.registry import registry
from shared.enums import EnvelopeType
from shared.protocol import make_envelope

router = APIRouter()

CONTROL_REQUIRED_ACTIONS = {
    "start_app",
    "stop_app",
    "start_application",
    "stop_application",
    "stop_process",
    "start_live_screen",
    "screen_start",
    "capture_screen",
    "input_event",
    "file_put",
    "file_get",
    "webcam",
    "webcam_start",
    "webcam_stop",
    "webcam_snapshot",
    "power",
    "power_restart",
    "power_shutdown",
    "power_cancel",
}


async def has_active_controller_lock(machine_id: str, user_id: str | int | None) -> bool:
    active = await active_control_session(machine_id)
    return active is not None and str(active.get("controller_user_id")) == str(user_id)


def command_requires_control(envelope_type: EnvelopeType | str, payload: dict) -> bool:
    if envelope_type in {EnvelopeType.INPUT_EVENT, EnvelopeType.FILE_DISPATCH}:
        return True
    return str(payload.get("action") or "") in CONTROL_REQUIRED_ACTIONS


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
        machine_info = first.payload.get("machine_info") or {}
        await registry.register_agent(machine_id, websocket)
        await update_machine_status(machine_id, "online", machine_info)
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
                registry.touch_heartbeat(machine_id)
                await update_machine_status(machine_id, "online")
                await websocket.send_json(make_envelope("ack", machine_id=machine_id, payload={"heartbeat": "ok"}))
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        for removed_machine_id in registry.unregister_agent(websocket):
            await update_machine_status(removed_machine_id, "offline")


@router.websocket("/admin")
@router.websocket("/ws/admin")
async def admin_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        query_ticket = websocket.query_params.get("ticket")
        if query_ticket:
            ticket = query_ticket
        else:
            first = parse_message(await websocket.receive_json())
            if first.type != EnvelopeType.AUTH:
                await websocket.send_json(error_message("first message must be auth"))
                return
            ticket = first.payload.get("ws_ticket", "")
        claims = await validate_ws_ticket(ticket)
        if claims is None:
            await websocket.send_json(error_message("invalid or expired ws ticket"))
            return
        await registry.register_admin(websocket, str(claims.get("user_id") or claims.get("username")), bool(claims.get("can_control")))
        await websocket.send_json(make_envelope("ack", payload={"role": "admin"}))
        while True:
            envelope = parse_message(await websocket.receive_json())
            machine_id = envelope.machine_id
            if envelope.type == EnvelopeType.SUBSCRIBE_MACHINE:
                want_control = bool(envelope.payload.get("control", False))
                if want_control and not bool(claims.get("can_control")):
                    await websocket.send_json(make_envelope("error", machine_id=machine_id, payload={"role": "control permission denied", "detail": "control permission denied"}))
                    continue
                if want_control and not await has_active_controller_lock(machine_id or "", claims.get("user_id")):
                    audit_bridge.enqueue(
                        {
                            "event_type": "control_denied",
                            "summary": "Relay control denied without active API lock",
                            "machine_id": machine_id,
                            "actor_type": "admin",
                            "actor_user_id": int(claims["user_id"]) if str(claims.get("user_id", "")).isdigit() else None,
                        }
                    )
                    await websocket.send_json(make_envelope("error", machine_id=machine_id, payload={"detail": "control_session_required"}))
                    continue
                ok, role = registry.subscribe(websocket, machine_id or "", want_control)
                audit_bridge.enqueue(
                    {
                        "event_type": "control_claimed" if ok and role == "controller" else "machine_selected",
                        "summary": f"Admin subscribed as {role}",
                        "machine_id": machine_id,
                        "actor_type": "admin",
                        "actor_user_id": int(claims["user_id"]) if str(claims.get("user_id", "")).isdigit() else None,
                    }
                )
                await websocket.send_json(
                    make_envelope("ack" if ok else "error", machine_id=machine_id, payload={"role": role, "detail": role})
                )
            elif envelope.type in {EnvelopeType.COMMAND, EnvelopeType.INPUT_EVENT, EnvelopeType.FILE_DISPATCH}:
                if not machine_id or not registry.is_controller(websocket, machine_id):
                    await websocket.send_json(error_message("observer_only", machine_id=machine_id))
                    audit_bridge.enqueue({"event_type": "control_denied", "summary": "Observer command rejected", "machine_id": machine_id, "actor_type": "admin"})
                    continue
                if command_requires_control(envelope.type, envelope.payload) and not await has_active_controller_lock(machine_id, claims.get("user_id")):
                    await websocket.send_json(error_message("controller lock required", machine_id=machine_id))
                    audit_bridge.enqueue(
                        {
                            "event_type": "control_denied",
                            "summary": "Active API control lock required",
                            "machine_id": machine_id,
                            "actor_type": "admin",
                            "actor_user_id": int(claims["user_id"]) if str(claims.get("user_id", "")).isdigit() else None,
                        }
                    )
                    continue
                if envelope.type == EnvelopeType.INPUT_EVENT:
                    audit_bridge.enqueue(
                        {
                            "event_type": "input_event_sent",
                            "summary": "Input event forwarded",
                            "machine_id": machine_id,
                            "actor_type": "admin",
                            "metadata": {"event": envelope.payload.get("event"), "count": 1},
                        }
                    )
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
        controlled = registry.controlled_machines_for(websocket)
        registry.unregister_admin(websocket)
        for machine_id, user_id in controlled:
            await release_control_session(machine_id, user_id)
