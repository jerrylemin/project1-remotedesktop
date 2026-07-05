from __future__ import annotations

import os

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from apps.relay.api_client import (
    active_control_session,
    authorize_command,
    record_agent_consent_decision,
    release_control_session,
    update_machine_status,
    validate_ws_ticket,
)
from apps.relay.config import get_relay_settings
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
    "webcam_devices",
    "keylogger_start",
    "keylogger_stop",
    "keylogger_events",
    "keylogger_export",
    "power",
    "power_restart",
    "power_shutdown",
    "power_cancel",
}


def agent_message_matches_machine(authenticated_machine_id: str, envelope_machine_id: str | None) -> bool:
    return envelope_machine_id in {None, authenticated_machine_id}


def admin_origin_allowed(origin: str | None, allowed_origins: set[str]) -> bool:
    return origin is None or origin in allowed_origins


def command_consent_binding(payload: dict) -> tuple[str, dict] | None:
    action = str(payload.get("action") or "")
    if action == "start_application":
        return "APPLICATION_START", {"name": payload.get("name") or payload.get("app_key"), "confirm": bool(payload.get("confirm"))}
    if action == "stop_application":
        return "APPLICATION_STOP", {"name": payload.get("name"), "confirm": bool(payload.get("confirm"))}
    if action == "stop_process":
        return "PROCESS_KILL", {"pid": int(payload.get("pid") or 0), "name": payload.get("name"), "confirm": bool(payload.get("confirm"))}
    if action == "screen_start":
        return "LIVE_SCREEN_START", {"mode": payload.get("mode") or "live", "consent": bool(payload.get("consent"))}
    if action == "screen_stop":
        return "LIVE_SCREEN_STOP", {"mode": payload.get("mode") or "live", "consent": bool(payload.get("consent"))}
    if action == "capture_screen":
        return "SCREENSHOT", {"mode": "screenshot", "consent": bool(payload.get("consent"))}
    if action == "webcam_devices":
        return "WEBCAM_ENUMERATE", {}
    if action == "webcam":
        command_type = "WEBCAM_START" if payload.get("start") else "WEBCAM_STOP"
        return command_type, {"consent": bool(payload.get("consent")), "device_id": payload.get("device_id")}
    if action == "webcam_snapshot":
        return "WEBCAM_START", {"consent": bool(payload.get("consent")), "device_id": payload.get("device_id")}
    if action == "keylogger_start":
        return "KEYLOGGER_START", {"session_id": payload.get("session_id"), "ttl_seconds": int(payload.get("ttl_seconds") or 60), "consent": bool(payload.get("consent"))}
    if action in {"keylogger_stop", "keylogger_export"}:
        return action.upper(), {"session_id": payload.get("session_id"), "consent": bool(payload.get("consent"))}
    if action == "remote_files_list":
        return "FILE_LIST", {"root_path": payload.get("root_path"), "relative_path": payload.get("relative_path") or "", "consent": bool(payload.get("consent"))}
    if action == "remote_file_download":
        return "FILE_DOWNLOAD", {"root_path": payload.get("root_path"), "relative_path": payload.get("relative_path") or "", "consent": bool(payload.get("consent"))}
    if action == "file_get":
        return "FILE_DOWNLOAD", {"path": payload.get("path")}
    if action == "power" and str(payload.get("power_action") or "").lower() in {"restart", "shutdown"}:
        power_action = str(payload["power_action"]).lower()
        return f"POWER_{power_action.upper()}", {"action": power_action, "confirm": bool(payload.get("confirm")), "reason": str(payload.get("reason") or "")}
    return None


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
        if not await validate_agent_secret(machine_id or "", machine_secret):
            await websocket.send_json(error_message("invalid machine secret", machine_id=machine_id))
            return
        machine_info = first.payload.get("machine_info") or {}
        if machine_info.get("os") == "FakeOS Demo" and os.getenv("TELEPC_ALLOW_DEMO", "false").lower() not in {"1", "true", "yes"}:
            await websocket.send_json(error_message("demo agents disabled", machine_id=machine_id))
            return
        await registry.register_agent(machine_id, websocket)
        await update_machine_status(machine_id, "online", machine_info)
        await websocket.send_json(make_envelope("ack", machine_id=machine_id, payload={"role": "agent"}))
        while True:
            envelope = parse_message(await websocket.receive_json())
            if not registry.is_current_agent(machine_id or "", websocket):
                continue
            if not agent_message_matches_machine(machine_id or "", envelope.machine_id):
                continue
            if envelope.type == EnvelopeType.FRAME:
                for subscriber in registry.subscribers_for(envelope.machine_id or machine_id):
                    await registry.send_json_safe(subscriber, envelope.model_dump(mode="json"))
            elif envelope.type in {EnvelopeType.COMMAND_RESULT, EnvelopeType.JOB_STATUS, EnvelopeType.AUDIT_EVENT}:
                if envelope.type == EnvelopeType.COMMAND_RESULT:
                    result = envelope.payload.get("result") or {}
                    consent_id = str(result.get("consent_id") or "")
                    decision = str(result.get("decision") or "")
                    if consent_id and decision and not await record_agent_consent_decision(machine_id or "", consent_id, decision):
                        envelope = parse_message(error_message("agent consent decision could not be recorded", machine_id=machine_id))
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
    if not admin_origin_allowed(websocket.headers.get("origin"), get_relay_settings().origin_set):
        await websocket.close(code=1008, reason="origin not allowed")
        return
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
                    await websocket.send_json(error_message("observer_only", machine_id=machine_id, session_id=envelope.session_id))
                    audit_bridge.enqueue({"event_type": "control_denied", "summary": "Observer command rejected", "machine_id": machine_id, "actor_type": "admin"})
                    continue
                if command_requires_control(envelope.type, envelope.payload) and not await has_active_controller_lock(machine_id, claims.get("user_id")):
                    await websocket.send_json(error_message("controller lock required", machine_id=machine_id, session_id=envelope.session_id))
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
                binding = command_consent_binding(envelope.payload) if envelope.type == EnvelopeType.COMMAND else None
                if binding and not await authorize_command(
                    machine_id,
                    claims.get("user_id"),
                    str(envelope.payload.get("_command_id") or ""),
                    binding[0],
                    binding[1],
                ):
                    await websocket.send_json(error_message("approved exact consent required", machine_id=machine_id, session_id=envelope.session_id))
                    audit_bridge.enqueue(
                        {
                            "event_type": "consent_blocked",
                            "summary": f"Relay blocked {binding[0]} without matching approved consent",
                            "machine_id": machine_id,
                            "actor_type": "admin",
                            "actor_user_id": int(claims["user_id"]) if str(claims.get("user_id", "")).isdigit() else None,
                        }
                    )
                    continue
                agent = registry.agent_for(machine_id)
                if agent is None:
                    await websocket.send_json(error_message("agent offline", machine_id=machine_id, session_id=envelope.session_id))
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
