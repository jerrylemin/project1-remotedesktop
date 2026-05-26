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
- Root `main.py` starts the complete demo stack from one terminal, binds to LAN by default, reuses already-running API/relay ports, and best-effort opens Windows Firewall for ports 8000/8001.
- Root `client.py` lets an authorized test machine connect to the main TelePC controller with one command and waits/retries while the main stack starts.
- Pytest uses a temp SQLite database instead of the runtime `telepc.db`, which keeps tests isolated and reliable on network-share workspaces.

## Partial / Demo-Level

- Real agent optional dependency fallback is tested, but physical Windows lab validation is still pending.

## Verification

- `py -3.12 -m compileall .` passed.
- `py -3.12 -m pytest -q` passed: 72 tests after the real-machine completion pass.
- `main.py --no-agents` plus `client.py --mode fake` smoke test passed with the client visible online in `/api/machines`.
- Default `python` is 3.10 on this workstation; use Python 3.11+ for this repo.

## Real-Machine Completion Pass (2026-05-26)

- Admin pages now require the HttpOnly session cookie; anonymous users redirect to `/admin/login`, and role denials render `403.html`.
- Relay command forwarding now checks the API's active control session before protected actions and releases the DB lock when a controlling admin WebSocket disconnects.
- Screen frames now use the requested frame schema with `data`, dimensions, `frame_no`, and `created_at`; fake mode remains deterministic.
- Real input is implemented behind `TELEPC_ENABLE_REAL_INPUT=true`; default mode records event summaries without key contents.
- Application/process providers use psutil when available, with allowlisted app start and protected process guards.
- File put/get helpers verify SHA256 and enforce sandbox path containment.
- Sandbox jobs enforce allowlisted runners, timeout reporting, and 64 KB output truncation.
- Webcam snapshot/start remains consent-gated; fake frames are available for CI.
- Power commands are demo-safe unless `TELEPC_ENABLE_REAL_POWER=true`.
- LAN helper scripts and `docs/REAL_MACHINE_TEST_CHECKLIST.md` were added.
