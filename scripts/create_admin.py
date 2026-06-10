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
    parser.add_argument("--include-demo-machines", action="store_true", help="Seed fake demo machines for local demos only.")
    args = parser.parse_args()
    asyncio.run(seed_admin(args.username, args.password, include_demo_machines=args.include_demo_machines))
    print(f"Admin user ready: {args.username}")


if __name__ == "__main__":
    main()
