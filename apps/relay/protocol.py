from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from shared.protocol import Envelope, make_envelope


def parse_message(data: dict[str, Any]) -> Envelope:
    try:
        return Envelope.model_validate(data)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


def error_message(detail: str, machine_id: str | None = None, session_id: str | None = None) -> dict[str, Any]:
    return make_envelope("error", machine_id=machine_id, session_id=session_id, payload={"detail": detail})

