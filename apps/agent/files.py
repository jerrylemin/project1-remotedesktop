from __future__ import annotations

import base64
from pathlib import Path

from apps.agent.sandbox import safe_write


def write_dispatched_file(root: Path, machine_id: str, job_id: str, filename: str, content_b64: str) -> str:
    target = safe_write(root, machine_id, job_id, filename, base64.b64decode(content_b64))
    return str(target)

