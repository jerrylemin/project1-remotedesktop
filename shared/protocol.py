from __future__ import annotations

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from shared.enums import EnvelopeType
from shared.time_utils import utc_iso


class Envelope(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    type: EnvelopeType
    msg_id: str = Field(default_factory=lambda: str(uuid4()))
    machine_id: str | None = None
    session_id: str | None = None
    ts: str = Field(default_factory=utc_iso)
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("msg_id")
    @classmethod
    def msg_id_required(cls, value: str) -> str:
        if not value:
            raise ValueError("msg_id is required")
        return value


def make_envelope(
    msg_type: EnvelopeType | str,
    *,
    machine_id: str | None = None,
    session_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return Envelope(
        type=msg_type,
        machine_id=machine_id,
        session_id=session_id,
        payload=payload or {},
    ).model_dump(mode="json")

