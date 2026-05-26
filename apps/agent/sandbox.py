from __future__ import annotations

import os
from pathlib import Path


ALLOWED_EXTENSIONS = {".txt", ".csv", ".json", ".py", ".ps1", ".png", ".jpg", ".jpeg", ".pdf", ".zip"}


class SandboxError(ValueError):
    pass


def ensure_safe_relative_path(relative_path: str) -> Path:
    if relative_path.startswith(("./", ".\\", "../", "..\\")):
        raise SandboxError("dot segments are not allowed")
    path = Path(relative_path)
    if path.is_absolute():
        raise SandboxError("absolute paths are not allowed")
    if relative_path.startswith(("\\\\", "C:", "c:")):
        raise SandboxError("absolute paths are not allowed")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise SandboxError("dot segments are not allowed")
    if len(path.parts) != 1:
        raise SandboxError("nested paths and separators are not allowed")
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise SandboxError("file extension not allowed")
    return path


def job_sandbox(root: Path, machine_id: str, job_id: str) -> Path:
    base = (root / machine_id / job_id).resolve()
    root_resolved = root.resolve()
    try:
        base.relative_to(root_resolved)
    except ValueError as exc:
        raise SandboxError("sandbox escaped root") from exc
    base.mkdir(parents=True, exist_ok=True)
    return base


def safe_write(root: Path, machine_id: str, job_id: str, filename: str, data: bytes) -> Path:
    safe_name = ensure_safe_relative_path(filename)
    base = job_sandbox(root, machine_id, job_id)
    target = (base / safe_name).resolve()
    try:
        target.relative_to(base)
    except ValueError as exc:
        raise SandboxError("target escaped job sandbox") from exc
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(target, flags, 0o600), "wb") as handle:
        handle.write(data)
    return target
