from __future__ import annotations


def handle_input_event(payload: dict) -> dict:
    event_type = payload.get("event")
    if event_type == "keyboard":
        return {"handled": True, "metadata": {"event": "keyboard", "keystroke_content": "[not captured]"}}
    return {"handled": True, "metadata": {"event": event_type or "unknown"}}

