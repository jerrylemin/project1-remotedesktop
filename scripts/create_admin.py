from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.seed import seed_admin


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default="admin123")
    args = parser.parse_args()
    asyncio.run(seed_admin(args.username, args.password))
    print(f"Admin user ready: {args.username}")


if __name__ == "__main__":
    main()
