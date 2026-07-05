from __future__ import annotations

import os
from pathlib import Path

import pytest

from client import apply_lab_real_profile, parse_client_args, require_real_mode_confirmation, set_real_mode_environment


def test_default_client_mode_is_real() -> None:
    config = parse_client_args([])

    assert config.mode == "real"


def test_example_environment_keeps_production_defaults() -> None:
    example = Path(".env.example").read_text(encoding="utf-8")

    assert "AGENT_MODE=real" in example
    assert "APP_ALLOWLIST=zalo,discord,vscode,chrome,notepad" in example
    assert "TELEPC_ENABLE_REAL_INPUT=true" in example
    assert "TELEPC_ENABLE_REAL_POWER=true" in example
    assert "TELEPC_REAL_MODE_CONFIRMED=TELEPC_LAB_AUTHORIZED" in example


def test_default_real_mode_enables_real_input_and_power(monkeypatch) -> None:
    monkeypatch.delenv("TELEPC_ENABLE_REAL_INPUT", raising=False)
    monkeypatch.delenv("TELEPC_ENABLE_REAL_POWER", raising=False)
    monkeypatch.delenv("TELEPC_REAL_MODE_CONFIRMED", raising=False)
    config = parse_client_args(["--mode", "real"])

    require_real_mode_confirmation(config)
    set_real_mode_environment(config)

    assert os.environ["TELEPC_ENABLE_REAL_INPUT"] == "true"
    assert os.environ["TELEPC_ENABLE_REAL_POWER"] == "true"
    assert os.environ["TELEPC_REAL_MODE_CONFIRMED"] == "TELEPC_LAB_AUTHORIZED"


def test_demo_mode_requires_allow_demo(monkeypatch) -> None:
    monkeypatch.delenv("TELEPC_ALLOW_DEMO", raising=False)

    with pytest.raises(SystemExit, match="TELEPC_ALLOW_DEMO"):
        parse_client_args(["--mode", "demo"])


def test_demo_mode_allowed_by_explicit_env(monkeypatch) -> None:
    monkeypatch.setenv("TELEPC_ALLOW_DEMO", "true")
    config = parse_client_args(["--mode", "demo"])

    assert config.mode == "demo"


def test_lab_real_profile_sets_real_environment(monkeypatch) -> None:
    monkeypatch.delenv("TELEPC_ENABLE_REAL_INPUT", raising=False)
    monkeypatch.delenv("TELEPC_ENABLE_REAL_POWER", raising=False)
    config = parse_client_args(["--profile", "lab-real", "--confirm-real-mode", "TELEPC_LAB_AUTHORIZED"])

    config = apply_lab_real_profile(config)
    require_real_mode_confirmation(config)
    set_real_mode_environment(config)

    assert config.mode == "real"
    assert os.environ["TELEPC_ENABLE_REAL_INPUT"] == "true"
    assert os.environ["TELEPC_ENABLE_REAL_POWER"] == "true"


def test_ci_blocks_lab_real(monkeypatch) -> None:
    monkeypatch.setenv("CI", "true")
    config = parse_client_args(["--profile", "lab-real", "--confirm-real-mode", "TELEPC_LAB_AUTHORIZED"])

    with pytest.raises(SystemExit, match="CI"):
        apply_lab_real_profile(config)


def test_pre_enabled_real_power_does_not_require_confirmation_for_default_real_mode(monkeypatch) -> None:
    monkeypatch.setenv("TELEPC_ENABLE_REAL_POWER", "true")
    config = parse_client_args(["--mode", "real"])

    require_real_mode_confirmation(config)


def test_invalid_confirmation_is_rejected_for_explicit_lab_profile() -> None:
    config = parse_client_args(["--profile", "lab-real", "--confirm-real-mode", "wrong"])

    with pytest.raises(SystemExit, match="TELEPC_LAB_AUTHORIZED"):
        require_real_mode_confirmation(config)
