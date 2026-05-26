from __future__ import annotations

import os
from typing import Any


def real_input_enabled() -> bool:
    return os.getenv("TELEPC_ENABLE_REAL_INPUT", "false").lower() == "true"


def key_code_to_pyautogui(code: str) -> str:
    code = code.strip()
    if len(code) == 4 and code.startswith("Key"):
        return code[-1].lower()
    if len(code) == 6 and code.startswith("Digit"):
        return code[-1]
    if len(code) == 7 and code.startswith("Numpad"):
        return code[-1]
    mapping = {
        "Space": "space",
        "Enter": "enter",
        "Tab": "tab",
        "Backspace": "backspace",
        "Delete": "delete",
        "Escape": "esc",
        "ArrowLeft": "left",
        "ArrowRight": "right",
        "ArrowUp": "up",
        "ArrowDown": "down",
        "ShiftLeft": "shift",
        "ShiftRight": "shift",
        "ControlLeft": "ctrl",
        "ControlRight": "ctrl",
        "AltLeft": "alt",
        "AltRight": "alt",
        "MetaLeft": "winleft",
        "MetaRight": "winright",
        "CapsLock": "capslock",
    }
    if code.startswith("F") and code[1:].isdigit():
        return code.lower()
    return mapping.get(code, code.lower())


def _summary(payload: dict[str, Any]) -> dict[str, Any]:
    event = str(payload.get("event") or "unknown")
    summary: dict[str, Any] = {"handled": True, "event": event, "real_input_enabled": real_input_enabled()}
    if "x" in payload and "y" in payload:
        summary.update({"x": int(payload["x"]), "y": int(payload["y"])})
    if event.startswith("key"):
        summary["key_event_count"] = 1
    return summary


def handle_input_event(payload: dict[str, Any]) -> dict[str, Any]:
    summary = _summary(payload)
    if not real_input_enabled():
        summary["demo_safe"] = True
        return summary
    try:
        import pyautogui
    except ImportError:
        summary["error"] = "pyautogui_not_installed"
        return summary

    event = summary["event"]
    x = summary.get("x")
    y = summary.get("y")
    if event in {"mouse_move", "mousemove"} and x is not None and y is not None:
        pyautogui.moveTo(x, y)
    elif event in {"mouse_down", "mousedown"}:
        pyautogui.mouseDown(x=x, y=y)
    elif event in {"mouse_up", "mouseup"}:
        pyautogui.mouseUp(x=x, y=y)
    elif event in {"mouse_click", "click"}:
        pyautogui.click(x=x, y=y)
    elif event == "dblclick":
        pyautogui.doubleClick(x=x, y=y)
    elif event == "wheel":
        pyautogui.scroll(int(payload.get("delta_y") or payload.get("deltaY") or 0) * -1)
    elif event in {"key_down", "keydown"}:
        key = str(payload.get("key_code") or payload.get("code") or "")
        if key:
            pyautogui.keyDown(key_code_to_pyautogui(key))
    elif event in {"key_up", "keyup"}:
        key = str(payload.get("key_code") or payload.get("code") or "")
        if key:
            pyautogui.keyUp(key_code_to_pyautogui(key))
    summary["demo_safe"] = False
    return summary


def scale_coordinates(offset_x: float, offset_y: float, remote_width: int, remote_height: int, displayed_width: int, displayed_height: int) -> tuple[int, int]:
    return (
        round(offset_x * remote_width / max(1, displayed_width)),
        round(offset_y * remote_height / max(1, displayed_height)),
    )
