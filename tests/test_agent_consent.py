from __future__ import annotations

from datetime import datetime, timedelta, timezone

from apps.agent.consent import display_consent_prompt, show_consent_popup


def test_consent_prompt_defaults_to_denied_on_eof(monkeypatch) -> None:
    monkeypatch.setattr("builtins.input", lambda _prompt="": (_ for _ in ()).throw(EOFError()))
    request = {
        "id": "c1",
        "machine_id": "m1",
        "requested_by": "admin",
        "command_type": "LIVE_SCREEN",
        "reason": "class demo",
        "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
    }

    decision = display_consent_prompt(request)

    assert decision["consent_id"] == "c1"
    assert decision["decision"] == "denied"


def test_show_consent_popup_approves_with_yes_runner() -> None:
    decision = show_consent_popup({"id": "c1"}, popup_runner=lambda _request, _timeout: "approved")

    assert decision == {"consent_id": "c1", "decision": "approved"}


def test_show_consent_popup_denies_on_timeout_runner() -> None:
    decision = show_consent_popup({"id": "c1"}, popup_runner=lambda _request, _timeout: "timeout")

    assert decision == {"consent_id": "c1", "decision": "timeout"}


def test_show_consent_popup_denies_on_popup_exception() -> None:
    def fail(_request, _timeout):
        raise RuntimeError("gui unavailable")

    decision = show_consent_popup({"id": "c1"}, popup_runner=fail)

    assert decision == {"consent_id": "c1", "decision": "denied"}
