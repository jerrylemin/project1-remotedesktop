from __future__ import annotations

from apps.agent import key_capture
from apps.relay.registry import RelayRegistry
import pytest


class FakeSocket:
    def __init__(self) -> None:
        self.closed = False

    async def close(self, *args, **kwargs) -> None:
        self.closed = True


async def test_reconnecting_agent_replaces_and_closes_stale_socket() -> None:
    registry = RelayRegistry()
    old = FakeSocket()
    new = FakeSocket()

    await registry.register_agent("m1", old)
    await registry.register_agent("m1", new)

    assert old.closed is True
    assert registry.agent_for("m1") is new
    assert registry.is_current_agent("m1", old) is False
    assert registry.is_current_agent("m1", new) is True


def test_keylogger_consent_defaults_to_deny() -> None:
    key_capture.reset_key_capture_state()

    try:
        key_capture.start_key_capture_session(60, {}, session_id="s1")
    except PermissionError:
        pass
    else:
        raise AssertionError("missing approval must deny key capture")


def test_keylogger_ttl_has_independent_stop_timer(monkeypatch) -> None:
    callbacks = []

    class FakeTimer:
        def __init__(self, _seconds, callback) -> None:
            callbacks.append(callback)

        def start(self) -> None:
            return None

        def cancel(self) -> None:
            return None

    key_capture.reset_key_capture_state()
    monkeypatch.setattr(key_capture, "Timer", FakeTimer)
    key_capture.start_key_capture_session(1, {"approved": True}, session_id="s1")

    callbacks[0]()

    assert key_capture.get_key_capture_events("s1") == []
    assert key_capture._sessions["s1"].status == "expired"


def test_second_keylogger_session_is_rejected_while_one_is_active() -> None:
    key_capture.reset_key_capture_state()
    key_capture.start_key_capture_session(60, {"approved": True}, session_id="s1", machine_id="m1")

    with pytest.raises(RuntimeError, match="already active"):
        key_capture.start_key_capture_session(60, {"approved": True}, session_id="s2", machine_id="m1")

    key_capture.reset_key_capture_state()
