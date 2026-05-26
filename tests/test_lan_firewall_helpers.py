from __future__ import annotations

import importlib.util
from pathlib import Path


def test_check_server_network_imports_cleanly() -> None:
    spec = importlib.util.spec_from_file_location("check_server_network", Path("scripts/check_server_network.py"))
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert callable(module.can_bind)


def test_start_server_windows_script_exists() -> None:
    text = Path("scripts/start_server_windows.ps1").read_text()
    assert "New-NetFirewallRule" in text
    assert "0.0.0.0" in text
