from __future__ import annotations

import base64

import pytest

from apps.agent.files import get_file
from apps.agent.sandbox import SandboxError


def test_download_sandbox_file_returns_bytes(tmp_path) -> None:
    root = tmp_path
    path = root / "m1" / "j1"
    path.mkdir(parents=True)
    (path / "test.txt").write_bytes(b"ok")
    result = get_file(root, "m1", "j1/test.txt")
    assert base64.b64decode(result["content_base64"]) == b"ok"


def test_download_traversal_rejected(tmp_path) -> None:
    with pytest.raises(SandboxError):
        get_file(tmp_path, "m1", "../secret.txt")
