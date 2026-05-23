# Feature Progress

## Completed In Current Milestone

- API server with auth, machine enrollment/list/detail, sessions, audit, files, and jobs endpoints.
- SQLAlchemy async models for requested tables plus one-time enroll tokens.
- Relay WebSocket endpoints `/ws/admin` and `/ws/agent`.
- In-memory relay registry, subscribers, and single-controller lock per machine.
- Fake agent with consent banner and fake JPEG frame generation.
- `create_admin.py` seeds `fake-machine-001` so dashboard is not empty for local demo.
- Agent sandbox traversal defense and overwrite prevention.
- Job runner allowlist and timeout handling.
- Process/application listing helpers with allowlist enforcement.
- Jinja admin UI pages for dashboard, machines, machine detail tabs, audit, files, webcam, and danger zone.
- Docs and tests.
- WebSocket auth hardened with short-lived single-use tickets from HttpOnly session.
- Relay internal API secret and background audit bridge.
- Persisted machine online/stale/offline status transitions.
- Provider abstractions for real/fake/fallback agent operations.
- Multi-machine fake demo script.

## Partial / Demo-Level

- Real agent optional dependency fallback is tested, but physical Windows lab validation is still pending.

## Verification

- `python -m compileall .` passed.
- `pytest -q` passed: 35 tests.
