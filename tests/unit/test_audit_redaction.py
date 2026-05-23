from __future__ import annotations

from shared.redaction import redact


def test_sensitive_fields_redacted() -> None:
    cleaned = redact({"password": "x", "nested": {"token": "y", "safe": "z"}, "keystroke_content": "abc"})
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["nested"]["token"] == "[REDACTED]"
    assert cleaned["nested"]["safe"] == "z"
    assert cleaned["keystroke_content"] == "[REDACTED]"

