from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def default_drive_roots() -> list[Path]:
    return [Path(f"{letter}:\\") for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ"]


def discover_allowed_remote_folders(drive_roots: list[Path] | None = None) -> list[dict[str, object]]:
    roots = drive_roots or default_drive_roots()
    folders: list[dict[str, object]] = []
    for drive_root in roots:
        root = Path(drive_root)
        drive_letter = root.drive[:1].upper() if root.drive else root.name[:1].upper()
        candidate = root / "Remote"
        if candidate.exists() and candidate.is_dir():
            folders.append({"root_path": str(candidate.resolve()), "exists": True, "drive_letter": drive_letter})
    return folders


def is_path_inside_allowed_root(root_path: str | Path, candidate_path: str | Path) -> bool:
    candidate_raw = Path(candidate_path)
    if str(candidate_raw).startswith("\\\\"):
        return False
    try:
        root = Path(root_path).resolve()
        candidate = candidate_raw.resolve()
        candidate.relative_to(root)
    except (OSError, ValueError):
        return False
    return True


def _resolve_relative(root_path: str | Path, relative_path: str = "") -> Path:
    if relative_path.startswith(("\\\\", "/", "\\")):
        raise PermissionError("absolute path rejected")
    relative = Path(relative_path)
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise PermissionError("path traversal rejected")
    root = Path(root_path).resolve()
    candidate = (root / relative).resolve()
    if not is_path_inside_allowed_root(root, candidate):
        raise PermissionError("path escapes allowed root")
    return candidate


def list_files_in_allowed_folder(root_path: str | Path, relative_path: str = "") -> list[dict[str, object]]:
    target = _resolve_relative(root_path, relative_path)
    if not target.exists() or not target.is_dir():
        raise FileNotFoundError("allowed folder path not found")
    rows: list[dict[str, object]] = []
    for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        if not is_path_inside_allowed_root(root_path, child):
            continue
        stat = child.stat()
        rows.append(
            {
                "name": child.name,
                "relative_path": str(child.relative_to(Path(root_path).resolve())),
                "entry_type": "directory" if child.is_dir() else "file",
                "size_bytes": None if child.is_dir() else stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            }
        )
    return rows


def download_allowed_file(root_path: str | Path, relative_path: str) -> tuple[str, bytes]:
    target = _resolve_relative(root_path, relative_path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("allowed file not found")
    return target.name, target.read_bytes()
