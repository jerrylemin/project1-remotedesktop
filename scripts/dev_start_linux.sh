#!/usr/bin/env bash
set -euo pipefail
python scripts/create_admin.py
python scripts/run_api.py &
python scripts/run_relay.py &
python scripts/run_fake_agent.py &
wait
