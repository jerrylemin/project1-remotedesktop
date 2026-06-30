from __future__ import annotations

from pathlib import Path


def test_remote_file_ui_has_no_free_root_path_textbox() -> None:
    html = Path("apps/api/templates/machine_detail.html").read_text(encoding="utf-8")

    assert "remote-root-list" in html
    assert "remote-files-output" in html
    assert "root_path" not in html
    assert "remote-root-input" not in html


def test_remote_file_ui_uses_agent_returned_roots() -> None:
    js = Path("apps/api/static/js/machine_detail.js").read_text(encoding="utf-8")

    assert "remote-files/folders" in js
    assert "result.allowed_folders" in js
    assert "data-remote-root" in js
    assert "C:\\\\Remote" not in js
