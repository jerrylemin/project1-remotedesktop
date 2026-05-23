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

## Partial / Demo-Level

- Real agent uses optional libraries (`mss`, `psutil`, etc.) when installed; fake mode is the verified path.
- Browser WebSocket token handling is basic; API endpoints are tested with bearer tokens.
- Relay audit bridge is a non-blocking stub ready for an internal API endpoint.

## Verification

- `python -m compileall .` passed.
- `pytest -q` passed: 21 tests.
