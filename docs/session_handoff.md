# Session Handoff

Date: 2026-05-23

## Current State

The repo was initially empty. A runnable TelePC scaffold was implemented with API, relay, fake agent, UI, docs, and tests.

## Commands

```powershell
python -m pip install -r requirements.txt
python scripts/create_admin.py
python scripts/run_api.py
python scripts/run_relay.py
python scripts/run_fake_agent.py
python -m compileall .
pytest -q
```

## Verification

- `python -m compileall .`: passed.
- `pytest -q`: passed, `35 passed`, no FastAPI deprecation warnings.
- Smoke test passed: `create_admin.py` seeds admin plus `fake-machine-001`; API login and `/api/machines` returned the fake machine while API, relay, and fake agent were running.

## Hardening Update

- Commit message: `Harden remote desktop relay agent audit and sandbox`; final hash is reported in the session result.
- Replaced FastAPI `on_event` startup with lifespan.
- Added short-lived single-use WS tickets issued from the HttpOnly admin session.
- Relay validates WS tickets through API internal endpoint using `INTERNAL_API_SECRET`.
- Relay audit bridge now uses a background queue and retrying API posts.
- Machine status online/stale/offline persists to DB and writes audit only on transition.
- Agent now has provider abstractions for screen, process, app launch, webcam, input, and sandbox runner.
- Missing optional real-agent dependencies return clear provider errors instead of crashing.
- Machine detail UI now has audit filters, sandbox file metadata, and job history.
- Added `scripts/run_3_fake_agents.py`.

## Next Work

- Validate real-agent behavior on a physical Windows lab machine with optional dependencies installed.
- Harden Alembic async/sync migration execution if migrations are used beyond metadata create.
