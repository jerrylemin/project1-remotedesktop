from __future__ import annotations

import types

from apps.agent.input_provider import handle_input_event, key_code_to_pyautogui, scale_coordinates


def test_coordinate_scaling_math() -> None:
    assert scale_coordinates(320, 180, 1920, 1080, 640, 360) == (960, 540)


def test_input_demo_safe_by_default(monkeypatch) -> None:
    monkeypatch.delenv("TELEPC_ENABLE_REAL_INPUT", raising=False)
    result = handle_input_event({"event": "mouse_click", "x": 10, "y": 20})
    assert result["demo_safe"] is True
    assert result["event"] == "mouse_click"


def test_real_pyautogui_call_can_be_monkeypatched(monkeypatch) -> None:
    calls = []
    monkeypatch.setenv("TELEPC_ENABLE_REAL_INPUT", "true")
    monkeypatch.setitem(__import__("sys").modules, "pyautogui", types.SimpleNamespace(click=lambda x=None, y=None: calls.append((x, y))))
    result = handle_input_event({"event": "mouse_click", "x": 7, "y": 9})
    assert calls == [(7, 9)]
    assert result["demo_safe"] is False


def test_keyboard_code_mapping_and_forwarding(monkeypatch) -> None:
    calls = []
    monkeypatch.setenv("TELEPC_ENABLE_REAL_INPUT", "true")
    monkeypatch.setitem(__import__("sys").modules, "pyautogui", types.SimpleNamespace(keyDown=lambda key: calls.append(("down", key)), keyUp=lambda key: calls.append(("up", key))))
    assert key_code_to_pyautogui("KeyA") == "a"
    assert key_code_to_pyautogui("Digit1") == "1"
    handle_input_event({"event": "key_down", "code": "KeyA"})
    handle_input_event({"event": "key_up", "code": "KeyA"})
    assert calls == [("down", "a"), ("up", "a")]
