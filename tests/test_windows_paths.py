from __future__ import annotations

from pathlib import Path

import pytest

from apps.agent.remote_files import _resolve_relative, download_file_from_allowed_root


@pytest.mark.parametrize("relative_path", ["CON", "NUL.txt", "PRN", "AUX.log", "COM1", "LPT9.txt", "folder\\CON"])
def test_windows_reserved_device_names_are_rejected(tmp_path: Path, relative_path: str) -> None:
    with pytest.raises(PermissionError, match="reserved"):
        _resolve_relative(tmp_path, relative_path, require_discovered=False)


def test_remote_download_rejects_file_over_limit(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "large.bin"
    target.write_bytes(b"12345")
    monkeypatch.setenv("TELEPC_MAX_REMOTE_DOWNLOAD_BYTES", "4")

    with pytest.raises(ValueError, match="too large"):
        download_file_from_allowed_root(str(tmp_path), "large.bin", require_discovered=False)
