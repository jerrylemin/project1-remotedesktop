from __future__ import annotations

import pytest
from pydantic import ValidationError

from shared.protocol import Envelope, make_envelope


def test_envelope_validation() -> None:
    envelope = Envelope.model_validate(make_envelope("heartbeat", payload={"ok": True}))
    assert envelope.type == "heartbeat"
    assert envelope.payload["ok"] is True


def test_envelope_rejects_unknown_type() -> None:
    with pytest.raises(ValidationError):
        Envelope.model_validate({"type": "bad", "msg_id": "1", "ts": "now", "payload": {}})

