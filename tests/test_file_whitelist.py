from __future__ import annotations

from pathlib import Path

import pytest

from apps.agent.commands import handle_command
from apps.agent.remote_files import discover_allowed_remote_folders, is_path_inside_allowed_root, list_files_in_allowed_folder


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


def test_list_files_blocks_escape(tmp_path: Path) -> None:
    root = tmp_path / "C" / "Remote"
    root.mkdir(parents=True)
    (root / "ok.txt").write_text("ok", encoding="utf-8")

    rows = list_files_in_allowed_folder(root, "")

    assert rows[0]["name"] == "ok.txt"
    with pytest.raises(PermissionError):
        list_files_in_allowed_folder(root, "..")


async def test_agent_remote_file_list_requires_consent(tmp_path: Path) -> None:
    root = tmp_path / "C" / "Remote"
    root.mkdir(parents=True)

    with pytest.raises(PermissionError, match="consent"):
        await handle_command("m1", {"action": "remote_files_list", "root_path": str(root), "relative_path": "", "consent": False}, tmp_path)
