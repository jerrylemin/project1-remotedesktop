from __future__ import annotations

import base64
import hashlib

import pytest

from apps.agent.files import put_file
from apps.agent.sandbox import SandboxError


def test_agent_file_put_writes_and_verifies_sha(tmp_path) -> None:
    data = b"hello"
    result = put_file(tmp_path, "m1", "j1", "test.txt", base64.b64encode(data).decode(), hashlib.sha256(data).hexdigest())
    assert result["sha256"] == hashlib.sha256(data).hexdigest()
    assert (tmp_path / result["saved_path"]).read_bytes() == data


def test_agent_file_put_sha_mismatch_rejected(tmp_path) -> None:
    with pytest.raises(SandboxError):
        put_file(tmp_path, "m1", "j1", "test.txt", base64.b64encode(b"x").decode(), "bad")
