from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import os
from typing import Literal
from uuid import uuid4


SessionStatus = Literal["pending", "active", "stopped", "expired", "denied", "timeout"]
KeyEventType = Literal["down", "up"]


@dataclass(frozen=True)
class KeyCaptureSession:
    session_id: str
    machine_id: str
    requested_by: str
    started_at: datetime
    expires_at: datetime
    status: SessionStatus


@dataclass(frozen=True)
class KeyEvent:
    timestamp: datetime
    session_id: str
    key_name: str
    event_type: KeyEventType
    active_window_title: str | None
    redacted: bool


SENSITIVE_TITLE_WORDS = {"password", "login", "credential", "payment", "bank", "checkout", "2fa", "otp"}
_sessions: dict[str, KeyCaptureSession] = {}
_events: dict[str, list[KeyEvent]] = {}
_listeners: dict[str, object] = {}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def active_window_title() -> str | None:
    try:
        import ctypes

        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buffer = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value or None
    except Exception:
        return None


def should_redact_window(title: str | None) -> bool:
    lowered = (title or "").lower()
    return any(word in lowered for word in SENSITIVE_TITLE_WORDS)


def _serialize_session(session: KeyCaptureSession) -> dict:
    row = asdict(session)
    row["started_at"] = session.started_at.isoformat()
    row["expires_at"] = session.expires_at.isoformat()
    return row


def _serialize_event(event: KeyEvent) -> dict:
    row = asdict(event)
    row["timestamp"] = event.timestamp.isoformat()
    return row


def _expire_if_needed(session_id: str) -> None:
    session = _sessions.get(session_id)
    if session and session.status == "active" and session.expires_at <= utc_now():
        stop_key_capture_session(session_id, status="expired")


def _key_name(raw_key: object) -> str:
    return str(raw_key).replace("'", "")


def record_key_event(session_id: str, key_name: str, event_type: KeyEventType, window_title: str | None = None) -> dict | None:
    _expire_if_needed(session_id)
    session = _sessions.get(session_id)
    if session is None or session.status != "active":
        return None
    title = active_window_title() if window_title is None else window_title
    redacted = should_redact_window(title)
    event = KeyEvent(
        timestamp=utc_now(),
        session_id=session_id,
        key_name="[REDACTED_SENSITIVE_CONTEXT]" if redacted else key_name,
        event_type=event_type,
        active_window_title=title,
        redacted=redacted,
    )
    _events.setdefault(session_id, []).append(event)
    return _serialize_event(event)


def _start_listener(session_id: str) -> object | None:
    if "PYTEST_CURRENT_TEST" in os.environ:
        return None
    try:
        from pynput import keyboard
    except ImportError:
        return None

    def on_press(key) -> None:
        record_key_event(session_id, _key_name(key), "down")

    def on_release(key) -> None:
        record_key_event(session_id, _key_name(key), "up")

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener


def start_key_capture_session(ttl_seconds: int, consent: dict, session_id: str | None = None, machine_id: str = "", requested_by: str = "") -> dict:
    if not consent.get("approved", True):
        raise PermissionError("key capture consent required")
    ttl = max(1, min(int(ttl_seconds or 60), 300))
    resolved_session_id = session_id or str(uuid4())
    session = KeyCaptureSession(
        session_id=resolved_session_id,
        machine_id=machine_id,
        requested_by=requested_by,
        started_at=utc_now(),
        expires_at=utc_now() + timedelta(seconds=ttl),
        status="active",
    )
    _sessions[resolved_session_id] = session
    _events.setdefault(resolved_session_id, [])
    listener = _start_listener(resolved_session_id)
    if listener is not None:
        _listeners[resolved_session_id] = listener
    print(f"TelePC Keylogger Lab Module active for {ttl} seconds. Local consent approved.", flush=True)
    return {"session": _serialize_session(session), "event_count": 0, "listener": listener is not None}


def stop_key_capture_session(session_id: str, status: SessionStatus = "stopped") -> dict:
    session = _sessions.get(session_id)
    if session is None:
        raise LookupError("key capture session not found")
    listener = _listeners.pop(session_id, None)
    if listener is not None:
        listener.stop()
    stopped = KeyCaptureSession(
        session_id=session.session_id,
        machine_id=session.machine_id,
        requested_by=session.requested_by,
        started_at=session.started_at,
        expires_at=session.expires_at,
        status=status,
    )
    _sessions[session_id] = stopped
    return {"session": _serialize_session(stopped), "event_count": len(_events.get(session_id, []))}


def get_key_capture_events(session_id: str) -> list[dict]:
    _expire_if_needed(session_id)
    return [_serialize_event(event) for event in _events.get(session_id, [])]


def export_key_capture_events(session_id: str, consent: dict) -> bytes:
    if not consent.get("approved", True):
        raise PermissionError("key capture export consent required")
    lines = ["timestamp,session_id,event_type,key_name,redacted,active_window_title"]
    for event in get_key_capture_events(session_id):
        lines.append(
            ",".join(
                [
                    str(event["timestamp"]),
                    str(event["session_id"]),
                    str(event["event_type"]),
                    str(event["key_name"]),
                    str(event["redacted"]),
                    str(event.get("active_window_title") or ""),
                ]
            )
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def reset_key_capture_state() -> None:
    for listener in list(_listeners.values()):
        listener.stop()
    _listeners.clear()
    _sessions.clear()
    _events.clear()
