from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLIENT_ENTRYPOINT = ROOT / "client.py"
DIST_DIR = ROOT / "dist"
BUILD_DIR = ROOT / "build" / "pyinstaller"
SPEC_DIR = ROOT / "build"
CLIENT_EXE = DIST_DIR / "TelePCClient.exe"


def pyinstaller_command() -> list[str]:
    return [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--clean",
        "--name",
        "TelePCClient",
        "--distpath",
        str(DIST_DIR),
        "--workpath",
        str(BUILD_DIR),
        "--specpath",
        str(SPEC_DIR),
        str(CLIENT_ENTRYPOINT),
    ]


def package_client_exe() -> Path:
    if not CLIENT_ENTRYPOINT.exists():
        raise FileNotFoundError(f"Client entrypoint not found: {CLIENT_ENTRYPOINT}")
    if importlib.util.find_spec("PyInstaller") is None:
        raise RuntimeError("PyInstaller is required: python -m pip install pyinstaller")
    subprocess.run(pyinstaller_command(), cwd=ROOT, check=True)
    if not CLIENT_EXE.exists():
        raise RuntimeError(f"Expected artifact was not created: {CLIENT_EXE}")
    return CLIENT_EXE


def main() -> int:
    artifact = package_client_exe()
    print(artifact)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
