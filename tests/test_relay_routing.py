from __future__ import annotations

from pathlib import Path

from apps.relay.router import admin_origin_allowed, agent_message_matches_machine


def test_browser_correlates_results_by_command_session_id() -> None:
    source = Path("apps/api/static/js/ws_client.js").read_text(encoding="utf-8")

    assert "session_id: sessionId" in source
    assert "this.resultWaiters = new Map()" in source
    assert "this.resultWaiters.get(msg.session_id)" in source
    assert "this.resultWaiters.shift()" not in source
    assert "rejectResultWaiters" in source


def test_agent_message_cannot_spoof_another_machine() -> None:
    assert agent_message_matches_machine("m1", "m1") is True
    assert agent_message_matches_machine("m1", None) is True
    assert agent_message_matches_machine("m1", "m2") is False


def test_admin_websocket_rejects_cross_origin_browser() -> None:
    allowed = {"http://localhost:8000"}

    assert admin_origin_allowed(None, allowed) is True
    assert admin_origin_allowed("http://localhost:8000", allowed) is True
    assert admin_origin_allowed("https://attacker.example", allowed) is False
