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
- Teacher prototype UI applied as real Jinja/static implementation.
- Bright dashboard and machines pages using live dashboard summary, machine list, and recent audit APIs.
- Dark per-machine remote shell with Applications, Processes, Screen, Files, Webcam, Keyboard Demo, Power, and Audit Logs modules.
- Shared WebSocket client for short-lived-ticket relay subscription and frame/command-result handling.
- Audited machine action endpoints for application, process, screen, webcam, power, sandbox files, and sandbox jobs.
- API and agent deny protected process stops for `lsass.exe`, `winlogon.exe`, `csrss.exe`, `services.exe`, `system`, and `registry`.
- Power actions require explicit confirmation and a non-empty reason.
- `docs/ui_prototype_mapping.md` documents how both teacher prototypes map to production files.

## Partial / Demo-Level

- Real agent optional dependency fallback is tested, but physical Windows lab validation is still pending.

## Verification

- `py -3.12 -m compileall .` passed.
- `py -3.12 -m pytest -q` passed: 42 tests.
- Default `python` is 3.10 on this workstation; use Python 3.11+ for this repo.
