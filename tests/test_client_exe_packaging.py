from __future__ import annotations

from pathlib import Path

from scripts.package_client_exe import CLIENT_ENTRYPOINT, CLIENT_EXE, pyinstaller_command


def test_build_client_exe_script_exists() -> None:
    script = Path("scripts/build_client_exe.ps1")

    assert script.exists()
    assert "scripts.package_client_exe" in script.read_text(encoding="utf-8")


def test_pyinstaller_onefile_command_targets_client() -> None:
    command = pyinstaller_command()

    assert "-m" in command
    assert "PyInstaller" in command
    assert "--onefile" in command
    assert "--name" in command
    assert "TelePCClient" in command
    assert str(CLIENT_ENTRYPOINT) in command


def test_expected_client_artifact_path_documented() -> None:
    assert CLIENT_EXE.name == "TelePCClient.exe"
    assert CLIENT_EXE.parent.name == "dist"


def test_client_entrypoint_is_real_client_not_fake_agent() -> None:
    source = CLIENT_ENTRYPOINT.read_text(encoding="utf-8")

    assert CLIENT_ENTRYPOINT.name == "client.py"
    assert "run_fake_agent" not in source
    assert "run_agent(settings)" in source
