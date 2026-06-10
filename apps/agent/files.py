from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from apps.agent.sandbox import SandboxError, safe_write


def write_dispatched_file(root: Path, machine_id: str, job_id: str, filename: str, content_b64: str) -> str:
    target = safe_write(root, machine_id, job_id, filename, base64.b64decode(content_b64))
    return str(target)


def put_file(root: Path, machine_id: str, job_id: str, filename: str, content_b64: str, expected_sha256: str | None = None) -> dict[str, object]:
    data = base64.b64decode(content_b64)
    sha256 = hashlib.sha256(data).hexdigest()
    if expected_sha256 and sha256 != expected_sha256:
        raise SandboxError("sha256 mismatch")
    target = safe_write(root, machine_id, job_id, filename, data)
    return {"saved_path": str(target.relative_to(root.resolve())), "sha256": sha256, "size": len(data)}


def get_file(root: Path, machine_id: str, relative_path: str) -> dict[str, object]:
    if relative_path.startswith(("../", "..\\", "\\\\", "/", "C:", "c:")):
        raise SandboxError("path traversal rejected")
    root_resolved = root.resolve()
    target = (root / machine_id / relative_path).resolve()
    try:
        target.relative_to(root_resolved / machine_id)
    except ValueError as exc:
        raise SandboxError("sandbox escaped root") from exc
    if target.is_symlink():
        raise SandboxError("symlink escapes are not allowed")
    data = target.read_bytes()
    return {"path": relative_path, "content_base64": base64.b64encode(data).decode(), "sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
