#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
SUBMISSION_DIR="$ROOT/artifacts/submission"
ZIP_PATH="$SUBMISSION_DIR/telepc_submission.zip"

mkdir -p "$SUBMISSION_DIR"
find "$ROOT" -type d -name __pycache__ -prune -exec rm -rf {} +
rm -rf "$ROOT/.pytest_cache" "$ROOT/.ruff_cache"
rm -f "$ROOT/telepc.db" "$ROOT/telepc.sqlite" "$ROOT/.env"
rm -f "$ZIP_PATH"

cd "$ROOT"
if command -v zip >/dev/null 2>&1; then
  zip -qr "$ZIP_PATH" . \
    -x ".git/*" \
    -x "artifacts/submission/*" \
    -x "__pycache__/*" \
    -x ".pytest_cache/*" \
    -x ".ruff_cache/*" \
    -x "graphify-out/*" \
    -x ".env" \
    -x "telepc.db" \
    -x "telepc.sqlite"
else
  python - <<'PY'
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

root = Path.cwd()
zip_path = root / "artifacts" / "submission" / "telepc_submission.zip"
exclude_parts = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "graphify-out"}
exclude_names = {".env", "telepc.db", "telepc.sqlite"}
with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if path.is_dir() or any(part in exclude_parts for part in rel.parts) or path.name in exclude_names:
            continue
        if rel.parts[:2] == ("artifacts", "submission"):
            continue
        zf.write(path, rel)
print(f"Submission zip created: {zip_path}")
PY
fi
