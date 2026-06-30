from __future__ import annotations

import os

import pytest

from client import apply_lab_real_profile, parse_client_args, require_real_mode_confirmation, set_real_mode_environment


def test_default_client_mode_is_real() -> None:
    config = parse_client_args([])

    assert config.mode == "real"


def test_real_mode_without_confirmation_does_not_enable_real_input_power() -> None:
    config = parse_client_args(["--mode", "real"])

    require_real_mode_confirmation(config)


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


def test_invalid_real_confirmation_rejected_when_real_power_requested(monkeypatch) -> None:
    monkeypatch.setenv("TELEPC_ENABLE_REAL_POWER", "true")
    config = parse_client_args(["--mode", "real", "--confirm-real-mode", "wrong"])

    with pytest.raises(SystemExit, match="TELEPC_LAB_AUTHORIZED"):
        require_real_mode_confirmation(config)
