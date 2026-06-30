from __future__ import annotations

from pathlib import Path

import pytest

from apps.agent import remote_files
from apps.agent.commands import handle_command
from apps.agent.remote_files import (
    discover_allowed_remote_folders,
    download_file_from_allowed_root,
    is_path_inside_allowed_root,
    list_files_in_allowed_root,
    require_discovered_allowed_root,
)


def test_existing_remote_folder_appears(tmp_path: Path) -> None:
    c_remote = tmp_path / "C" / "Remote"
    c_remote.mkdir(parents=True)

    folders = discover_allowed_remote_folders([tmp_path / "C", tmp_path / "D"])

    assert [folder["root_path"] for folder in folders] == [str(c_remote.resolve())]
    assert folders[0]["drive_letter"] == "C"


def test_missing_remote_folders_do_not_appear(tmp_path: Path) -> None:
    assert discover_allowed_remote_folders([tmp_path / "C"]) == []


def test_path_traversal_and_absolute_override_rejected(tmp_path: Path) -> None:
    root = tmp_path / "C" / "Remote"
    root.mkdir(parents=True)

    assert is_path_inside_allowed_root(root, root / "safe.txt") is True
    assert is_path_inside_allowed_root(root, root / ".." / "secret.txt") is False
    assert is_path_inside_allowed_root(root, Path(r"\\server\share\file.txt")) is False


def test_list_files_blocks_escape(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "C" / "Remote"
    root.mkdir(parents=True)
    (root / "ok.txt").write_text("ok", encoding="utf-8")
    monkeypatch.setattr(remote_files, "default_drive_roots", lambda: [tmp_path / "C"])

    rows = list_files_in_allowed_root(str(root), "")

    assert rows[0]["name"] == "ok.txt"
    with pytest.raises(PermissionError):
        list_files_in_allowed_root(str(root), "..")


def test_required_remote_roots_are_accepted_when_discovered(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    roots = []
    for letter in ("C", "D", "E", "Z"):
        root = tmp_path / letter / "Remote"
        root.mkdir(parents=True)
        roots.append(tmp_path / letter)
    monkeypatch.setattr(remote_files, "default_drive_roots", lambda: roots)

    for letter in ("C", "D", "E", "Z"):
        assert require_discovered_allowed_root(str(tmp_path / letter / "Remote")).exists()


def test_arbitrary_roots_are_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    allowed = tmp_path / "C" / "Remote"
    blocked = tmp_path / "C" / "Users"
    allowed.mkdir(parents=True)
    blocked.mkdir(parents=True)
    monkeypatch.setattr(remote_files, "default_drive_roots", lambda: [tmp_path / "C"])

    with pytest.raises(PermissionError):
        require_discovered_allowed_root(str(blocked))


def test_absolute_relative_path_and_symlink_escape_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "C" / "Remote"
    secret = tmp_path / "secret.txt"
    root.mkdir(parents=True)
    secret.write_text("secret", encoding="utf-8")
    monkeypatch.setattr(remote_files, "default_drive_roots", lambda: [tmp_path / "C"])

    with pytest.raises(PermissionError):
        list_files_in_allowed_root(str(root), str(tmp_path / "outside"))
    link = root / "link.txt"
    try:
        link.symlink_to(secret)
    except OSError:
        pytest.skip("symlink creation unavailable")
    assert list_files_in_allowed_root(str(root), "") == []


def test_download_from_allowed_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "C" / "Remote"
    root.mkdir(parents=True)
    (root / "ok.txt").write_text("ok", encoding="utf-8")
    monkeypatch.setattr(remote_files, "default_drive_roots", lambda: [tmp_path / "C"])

    assert download_file_from_allowed_root(str(root), "ok.txt") == b"ok"


async def test_agent_remote_file_list_requires_consent(tmp_path: Path) -> None:
    root = tmp_path / "C" / "Remote"
    root.mkdir(parents=True)

    with pytest.raises(PermissionError, match="consent"):
        await handle_command("m1", {"action": "remote_files_list", "root_path": str(root), "relative_path": "", "consent": False}, tmp_path)
