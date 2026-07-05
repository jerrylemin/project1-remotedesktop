from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re


@dataclass(frozen=True)
class AllowedFolder:
    root_path: str
    exists: bool
    drive_letter: str


@dataclass(frozen=True)
class RemoteFileEntry:
    name: str
    relative_path: str
    entry_type: str
    size_bytes: int | None
    modified_at: str


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
            folders.append(asdict(AllowedFolder(root_path=str(candidate.resolve()), exists=True, drive_letter=drive_letter)))
    return folders


def normalize_allowed_root(root_path: str) -> Path:
    if root_path.startswith("\\\\"):
        raise PermissionError("UNC root rejected")
    root = Path(root_path)
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError("allowed root not found")
    return root.resolve()


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(str(left.resolve())) == os.path.normcase(str(right.resolve()))


def require_discovered_allowed_root(root_path: str) -> Path:
    requested = normalize_allowed_root(root_path)
    for folder in discover_allowed_remote_folders():
        discovered = normalize_allowed_root(str(folder["root_path"]))
        if _same_path(requested, discovered):
            return discovered
    raise PermissionError("root is not an allowed Remote folder")


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


def _resolve_relative(root_path: str | Path, relative_path: str = "", *, require_discovered: bool = True) -> Path:
    if relative_path.startswith(("\\\\", "/", "\\")):
        raise PermissionError("absolute path rejected")
    relative = Path(relative_path)
    parts = [part for part in re.split(r"[\\/]", relative_path) if part]
    reserved = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
    if len(relative_path) > 240 or any(part.rstrip(". ").split(".", 1)[0].upper() in reserved or part != part.rstrip(". ") for part in parts):
        raise PermissionError("reserved or unsafe Windows path rejected")
    if relative.is_absolute() or any(part == ".." for part in relative.parts):
        raise PermissionError("path traversal rejected")
    root = require_discovered_allowed_root(str(root_path)) if require_discovered else Path(root_path).resolve()
    candidate = (root / relative).resolve()
    if not is_path_inside_allowed_root(root, candidate):
        raise PermissionError("path escapes allowed root")
    return candidate


def list_files_in_allowed_root(root_path: str, relative_path: str = "") -> list[dict[str, object]]:
    target = _resolve_relative(root_path, relative_path)
    if not target.exists() or not target.is_dir():
        raise FileNotFoundError("allowed folder path not found")
    rows: list[dict[str, object]] = []
    root = require_discovered_allowed_root(root_path)
    for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
        if not is_path_inside_allowed_root(root, child):
            continue
        stat = child.stat()
        rows.append(asdict(RemoteFileEntry(
            name=child.name,
            relative_path=str(child.relative_to(root)),
            entry_type="directory" if child.is_dir() else "file",
            size_bytes=None if child.is_dir() else stat.st_size,
            modified_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        )))
    return rows


def download_file_from_allowed_root(root_path: str, relative_path: str, *, require_discovered: bool = True) -> bytes:
    target = _resolve_relative(root_path, relative_path, require_discovered=require_discovered)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("allowed file not found")
    limit = max(1, int(os.getenv("TELEPC_MAX_REMOTE_DOWNLOAD_BYTES", str(10 * 1024 * 1024))))
    with target.open("rb") as handle:
        data = handle.read(limit + 1)
    if len(data) > limit:
        raise ValueError("remote file too large")
    return data


def list_files_in_allowed_folder(root_path: str | Path, relative_path: str = "") -> list[dict[str, object]]:
    return list_files_in_allowed_root(str(root_path), relative_path)


def download_allowed_file(root_path: str | Path, relative_path: str) -> tuple[str, bytes]:
    target = _resolve_relative(root_path, relative_path)
    return target.name, download_file_from_allowed_root(str(root_path), relative_path)
