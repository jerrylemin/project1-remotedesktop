from __future__ import annotations

import pytest

from apps.agent.sandbox import SandboxError, safe_write


@pytest.mark.parametrize("name", ["../x.py", "./x.py", "/tmp/x.py", "a/b.py", "evil.exe"])
def test_path_traversal_defense(tmp_path, name: str) -> None:
    with pytest.raises(SandboxError):
        safe_write(tmp_path, "machine", "job", name, b"data")


def test_safe_write_creates_inside_sandbox(tmp_path) -> None:
    target = safe_write(tmp_path, "machine", "job", "script.py", b"print('ok')")
    assert target.read_bytes() == b"print('ok')"
    assert target.relative_to(tmp_path.resolve())

