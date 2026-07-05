from __future__ import annotations

import argparse
import asyncio
import getpass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apps.api.seed import seed_admin


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="admin")
    parser.add_argument("--password", default=None, help="Optional; prompts securely when omitted.")
    parser.add_argument("--include-demo-machines", action="store_true", help="Seed fake demo machines for local demos only.")
    args = parser.parse_args()
    password = args.password or getpass.getpass("Admin password: ")
    if not password:
        raise SystemExit("Admin password cannot be empty.")
    asyncio.run(seed_admin(args.username, password, include_demo_machines=args.include_demo_machines))
    print(f"Admin user ready: {args.username}")


if __name__ == "__main__":
    main()
