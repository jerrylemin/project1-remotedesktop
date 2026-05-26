from __future__ import annotations

from apps.agent.input_provider import handle_input_event as safe_handle_input_event


def handle_input_event(payload: dict) -> dict:
    return safe_handle_input_event(payload)
