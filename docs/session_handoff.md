# Session Handoff

## Strict prompt packaging slice (2026-06-01)

Current status:

- Phase 0 context was rerun for the stricter TelePC prompt.
- Repo is not a Git checkout in this workspace; `git status --short` fails with "not a git repository".
- Graphify was refreshed with `graphify update .`; report now shows 1111 nodes and 3280 edges.
- Baseline verification passed on Python 3.11.9: `python -m compileall .`, `ruff check .`, and `python -m pytest -q` with 98 tests after adding packaging coverage.
- Added one-file Windows client packaging support:
  - `scripts/package_client_exe.py`
  - `scripts/build_client_exe.ps1`
  - `tests/test_client_exe_packaging.py`
- Focused packaging test passed: `4 passed`.
- `.\scripts\build_client_exe.ps1` built `dist\TelePCClient.exe`.
- `.\dist\TelePCClient.exe --help` passed.
- API smoke on port 8765 passed: `/health` 200, `/admin/login` 200, `/api/machines` unauthenticated 401.

2026-06-01 continuation:

- Production machine listing hides fake/demo machines by default.
- `seed_admin()` no longer creates fake machines unless explicitly requested; `main.py` starts fake agents only with `--demo-agents`.
- Application whitelist now matches Zalo, Discord, VSCode, Chrome, Notepad. API ignores raw app command strings and requires consent for start/stop.
- Agent and API now support `X:\Remote` whitelist file listing/download commands with consent gates.
- Agent and API now support webcam device enumeration and selected `device_id` before start.
- Agent consent now has a native Tkinter popup path with Yes, No, topmost window, timeout denial, and popup-failure denial.
- Verification: compileall passed, ruff passed, pytest passed with 118 tests, EXE rebuilt, `TelePCClient.exe --help` passed, API smoke passed.

Remaining strict-compliance blocker:

- Physical Windows lab validation of the rebuilt EXE, real popup focus behavior, real `X:\Remote` discovery, USB/built-in webcam enumeration, and live device start is still pending.

First command next:

```powershell
python -m pytest -q
```

## Defense Readiness Pass (2026-05-30)

Current status:

- Relay machine auth now verifies registered machine secrets through `/internal/machines/verify-secret`; failed and successful attempts are audited without secret values.
- `MachineGrant` is enforced for non-admin machine-scoped actions.
- Durable consent records and decision APIs exist; the UI relays consent requests to the visible agent prompt and records approve/deny before sensitive actions.
- Agent screen frames are command-gated and no longer stream immediately after websocket connection.
- Root `client.py` defaults to demo mode. Lab-real mode requires `--profile lab-real --confirm-real-mode TELEPC_LAB_AUTHORIZED` or `scripts/run_lab_real_client.ps1`.
- Real power execution also requires `TELEPC_REAL_MODE_CONFIRMED=TELEPC_LAB_AUTHORIZED` and is disabled under pytest.
- Added first-class allowlisted process start, `/health`, and submission cleanup scripts.

Verification:

- `python -m compileall .`: passed.
- `python -m pytest -q`: passed, 94 tests.
- `ruff check .`: passed.
- Smoke API: `/health` 200, `/admin/login` 200, unauthenticated `/api/machines` 401.

Next first command:

```powershell
python -m pytest -q
```

Files to read first next time:

- `docs/implementation_plan_10_10.md`
- `docs/final_compliance_report.md`
- `docs/security_consent_audit.md`

Date: 2026-05-26

## Current State

TelePC now has the teacher prototype UI applied as real FastAPI/Jinja pages and static assets. The existing backend, relay, fake agent, real-agent provider structure, auth, roles, audit logs, file sandbox, sessions, and controller lock flow were preserved.

## Commands

```powershell
python -m pip install -r requirements.txt
python scripts/create_admin.py
python scripts/run_api.py
python scripts/run_relay.py
python scripts/run_fake_agent.py
python scripts/run_3_fake_agents.py
py -3.12 main.py
py -3.12 -m compileall .
py -3.12 -m pytest -q
```

## Verification

- `py -3.12 -m compileall .`: passed.
- `py -3.12 -m pytest -q`: passed, `42 passed`.
- `py -3.12 main.py --no-agents --skip-firewall` plus `py -3.12 client.py --server 127.0.0.1 --machine-id CLIENT-SMOKE-01 --mode fake --connect-timeout 20`: passed; `CLIENT-SMOKE-01` appeared online through `/api/machines`.
- Default `python` on this machine is Python 3.10. It cannot run the suite because the project requires Python 3.11+ and imports `datetime.UTC`.

## Final Acceptance Check

- Pulled `origin/main`; repo was already current before final polish.
- Re-ran `py -3.12 -m compileall .`: passed.
- Re-ran `py -3.12 -m pytest -q`: passed, `42 passed`.
- Smoke demo with `py -3.12 scripts/create_admin.py`, API, relay, and `run_3_fake_agents.py` passed.
- Verified login page, dashboard, machines page, machine detail shell, fake screen frames over WebSocket, applications command result, processes command result, protected process denial, sandbox traversal block, file upload/dispatch, webcam consent text, Keyboard Demo scope text, power confirm/reason API, and per-machine audit logs.
- Fixed final UI wiring issue: command results from the agent are wrapped in `payload.result`, and `apps/api/static/js/machine_detail.js` now unwraps them before rendering Applications, Processes, Webcam, and Power results.
- Fixed shared topbar title rendering by changing the partial to page variables.
- Final commit message: `Finalize TelePC demo readiness`; final hash is reported in the session result.

## Startup Wrapper Update

- Added root `main.py`.
- `py -3.12 main.py` now binds API/relay to `0.0.0.0`, seeds the demo admin, starts the API on port 8000, starts the relay on port 8001, starts the three fake agents, prints local/LAN login URLs, and stops child processes on `Ctrl+C`.
- Use `py -3.12 main.py --no-agents` to start only API and relay.
- If API or relay is already listening on the selected ports, `main.py` reuses it and starts only missing services.
- On Windows, `main.py` best-effort adds inbound firewall rules for TCP `8000` and `8001`; if not running as Administrator it prints a clear note and keeps running.
- Verified `py -3.12 main.py` smoke startup: `/admin/login` loaded and `LAB-PC-01`, `LAB-PC-02`, and `HOME-PC-01` appeared online after login.

## Test Machine Client Update

- Added root `client.py`.
- On a test machine, run `py -3.12 client.py --server <MAIN_MACHINE_IP> --machine-id <NAME>`.
- Default mode is `real`; use `--mode fake` for demo-only client behavior.
- `client.py` waits/retries for API and relay instead of exiting immediately while the main machine is still starting.
- Real mode warns if optional dependencies for screen/process/webcam are missing.
- The client remains consent-visible and uses the existing sandbox, audit, relay, and demo-safe power behavior.

## Test Database Update

- `tests/conftest.py` now points pytest at a process-local SQLite database in the Windows temp directory before importing `apps.api.db`.
- This prevents tests from dropping tables in the runtime `telepc.db` and avoids SQLite disk I/O errors when the repo is running from a network share.

## Teacher Prototype UI Update

- Prototype files found in `docs/teacher_prototypes/`.
- `Topic01_Prototype.html` mapped to the bright dashboard, machines, audit index, shared sidebar/topbar, and dashboard CSS/JS.
- `remote_control_web_prototype.html` mapped to the dark machine detail remote shell, module sidebar, consent notices, confirm modal, relay client, and machine detail JS.
- Added `GET /api/dashboard/summary` and `GET /api/dashboard/recent-audit`.
- Added audited machine action endpoints for applications, processes, screen, webcam, power, sandbox files, and sandbox jobs.
- Protected process denial is enforced in the API and agent command handler.
- Power actions require `confirm` and a non-empty `reason`.
- Commit message: `Apply teacher prototype UI to remote desktop project`; final commit hash is reported in the session result.

## Files Changed

- API/backend: `apps/api/routers/dashboard.py`, `apps/api/routers/machines.py`, `apps/api/routers/admin_pages.py`, `apps/api/main.py`, `apps/api/schemas.py`, `apps/api/services/audit.py`.
- Agent safety/actions: `apps/agent/commands.py`, `apps/agent/providers.py`.
- Templates: `apps/api/templates/base.html`, `dashboard.html`, `machines.html`, `machine_detail.html`, `audit.html`, `partials/*`.
- Static assets: `apps/api/static/css/app.css`, `teacher_dashboard.css`, `teacher_remote_shell.css`, `apps/api/static/js/dashboard.js`, `machines.js`, `machine_detail.js`, `audit.js`, `files.js`, `ws_client.js`.
- Tests: `tests/conftest.py`, `tests/integration/test_teacher_ui_routes.py`, `tests/unit/test_process_commands.py`.
- Docs: `README.md`, `docs/report.md`, `docs/demo_script.md`, `docs/ui_prototype_mapping.md`, `docs/session_handoff.md`, `docs/feature_progress.md`.

## Next Work

- Validate real-agent behavior on a physical Windows lab machine with optional dependencies installed.
- Harden Alembic async/sync migration execution if migrations are used beyond metadata create.
- Consider a server-side relay command bridge if future UI actions must be initiated without browser WebSocket control.

## Real-Machine Completion Pass Handoff (2026-05-26)

Current state:

- Admin page auth guard, role 403 page, relay/API controller-lock sync, fake/real provider upgrades, file/job/webcam/power/input guards, LAN helper scripts, and expanded tests are implemented.
- `py -3.12 -m compileall .` passed.
- `py -3.12 -m pytest -q` passed: 72 tests.

Commands to run:

```powershell
py -3.12 -m compileall .
py -3.12 -m pytest -q
py -3.12 scripts/check_server_network.py
powershell -ExecutionPolicy Bypass -File scripts/start_server_windows.ps1 -FakeAgents
```

Unresolved risks:

- Physical Windows lab validation remains pending for real input, mss screen capture performance, OpenCV webcam capture, and real power execution.
- Large file dispatch currently emits a download URL field for files over 512 KB; signed download serving can be expanded later.
- Follow-up fix after real-machine logs: UI now requires an active claim before dispatching relay commands, checks webcam consent before calling the API, surfaces upload validation details, and routes file dispatch through `/api/machines/{id}/file-dispatch`.
- Follow-up lock fix: repeated `POST /api/sessions` by the same admin now returns the existing active session instead of `409`, preventing refresh/interrupted-browser stale self-locks. Different admins still receive `409`.
- Follow-up webcam fix: `webcam/start` now returns an initial preview frame, and the UI no longer overwrites webcam images with status text.
- Follow-up webcam live fix: agent now keeps OpenCV camera open during webcam sessions and streams `webcam_frame` envelopes continuously. Tunables: `TELEPC_WEBCAM_FPS` (default 15, max 30), `TELEPC_WEBCAM_JPEG_QUALITY` (default 55), `TELEPC_WEBCAM_WIDTH`/`HEIGHT` (default 640x360).
- Follow-up real keyboard fix: Keyboard Demo now forwards scoped key down/up events to the agent after Claim Control. Agent execution still requires `TELEPC_ENABLE_REAL_INPUT=true`; feed entries use key codes only and do not store typed characters.
- Follow-up input envelope fix: agent WebSocket now handles relay-forwarded `input_event` envelopes directly; before this, keyboard demo events reached the agent socket but were ignored because only `command` envelopes were processed.
- Follow-up controller-ack keyboard fix: the browser now waits until the relay acknowledges the admin WebSocket as `controller` before sending Keyboard Demo or mouse input events. Global page keyboard forwarding was removed; only the Keyboard Demo text box sends key codes.
- Follow-up power fix: `lock` and `cancel` power actions no longer require a reason; `restart` and `shutdown` still require checkbox confirmation plus a reason of at least 5 characters. The UI validates these rules before calling the API.

Commit hash:

- Final commit is the latest `main` commit with message `feat: complete real machine TelePC control (screen/input/files/webcam/power/audit)`. Use `git log --oneline -1` for the exact hash after commit creation.
