# Feature Progress

## One-file Server Startup (2026-07-05)

- `main.py` now detects whether an admin exists after database initialization.
- The first run securely prompts for and confirms an admin password; later runs start without prompting.
- Normal Server operation requires only `py -3.12 main.py`; API, relay, LAN firewall setup, and coordinated shutdown are handled together.
- Replaced the long Server/Client manual with a concise Vietnamese quick-start guide.
- Verification: focused launcher/auth tests passed, Ruff passed, compile passed, and the full suite passed with 221 tests.

## Automatic Real Control Defaults (2026-07-05)

- Real-mode `client.py` now enables real input and real power automatically without requiring the legacy profile flags.
- Server child processes receive the same enabled defaults.
- Direct agent providers default to real input/power outside pytest; tests and demo-safe paths remain protected.
- Existing consent, controller authorization, audit, power reason, and shutdown-delay controls remain enforced.

## Vietnamese Server/Client Guide (2026-07-05)

- Added `docs/HUONG_DAN_SU_DUNG_SERVER_CLIENT.md` with complete Server setup, secure enrollment, EXE/source Client launch, consent-driven operation, troubleshooting, shutdown, demo, and physical-evidence steps.
- Corrected stale README/setup references to implicit admin seeding and the removed `admin123` default.

## Bug Prevention Pass (2026-07-04)

- Added invariant, threat, bug-class, and test-gap registries.
- Prevented out-of-order result routing, stale agent sockets, cross-machine agent envelopes, and cross-origin admin WebSockets.
- Bound consent to exact raw payload plus command ID and retained single-use execution consumption.
- Added safe login throttling, explicit credential bootstrap, audit redaction/bounds, PID-reuse checks, process metric normalization, Windows path/size bounds, selected webcam snapshots, Keylogger independent TTL/one-session/disconnect cleanup, and invalid environment fallbacks.
- Final verification: compile PASS, Ruff PASS, 214 tests PASS, smoke 200/200/401, EXE build/help PASS.
- Physical Windows evidence remains absent; score is still capped at 96/100.

## Final Defense Re-audit (2026-07-04)

- Closed direct controller-WebSocket consent bypass and replay by consuming exact approved consent at the relay/API boundary.
- Moved local consent decision recording from browser JavaScript to the authenticated agent relay flow.
- Added distinct live-screen start/stop consent and fixed UI command dispatch.
- Aligned `.env.example` with real mode and the exact five-app whitelist.
- Fixed Windows application executable paths containing spaces.
- Final verification: compile PASS, Ruff PASS, 154 tests PASS, smoke 200/200/401, EXE build PASS, EXE help PASS.
- Score remains capped at 96/100 because all required physical Windows evidence files are missing.

## Loop Engineering Pass (2026-06-23)

- Raised the automated implementation state from the 74/100 audit baseline to a 96/100 capped state.
- Added strict agent-side `X:\Remote` folder discovery and validation; caller-supplied arbitrary roots, UNC roots, absolute relative-path overrides, traversal, missing roots, and symlink escapes are rejected.
- Bound consent to exact command payload hashes for application, process, screen, file, webcam, keylogger, and power actions.
- Replaced the browser Keyboard Demo path with a visible, consented, TTL-bound, in-memory Keylogger Lab Module; tests mock key events and never start real capture.
- Wired webcam device enumeration so the UI renders agent-returned devices and removed the static `Camera 0` fallback.
- Changed client defaults to real enrolled mode; demo mode now requires both `--mode demo` and `TELEPC_ALLOW_DEMO=true`.
- Added `scripts/run_physical_lab_validation.ps1` and `artifacts/physical_validation/README.md`.
- Verification: focused tests passed, full LOOP 7 verification passed with 147 tests, HTTP smoke passed, and `dist\TelePCClient.exe` was rebuilt successfully.
- Remaining blocker: physical Windows evidence is missing, so final score is capped at 96/100.

## Strict Consent Closure Slice (2026-06-13)

- Added `PROCESS_KILL` to the sensitive consent policy and enforced it on process stop routes.
- Added `WEBCAM_STOP` to the sensitive consent policy and enforced it on webcam stop routes.
- Machine detail UI now forwards local consent requests before process stop and webcam stop actions.
- Production dashboard and machines page empty-state copy now points to enrolled real client machines and `TelePCClient.exe`.
- Added regression tests for process stop consent and webcam stop consent.
- Verification: compileall passed, Ruff passed, pytest passed with 120 tests, EXE packaging passed, EXE `--help` passed, and HTTP smoke passed.

## Strict Prompt Packaging Slice (2026-06-01)

- Added `scripts/package_client_exe.py` with a `package_client_exe() -> Path` helper that invokes PyInstaller in one-file mode.
- Added `scripts/build_client_exe.ps1`; run `.\scripts\build_client_exe.ps1 -InstallPyInstaller` for the first build, then `.\scripts\build_client_exe.ps1` for repeat builds.
- Expected client artifact is `dist\TelePCClient.exe`.
- Added `tests/test_client_exe_packaging.py`.
- Verification: `python -m pytest tests/test_client_exe_packaging.py -q` passed, 4 tests.
- Packaging verification: `.\scripts\build_client_exe.ps1` built `dist\TelePCClient.exe`, and `.\dist\TelePCClient.exe --help` passed.
- Full verification after the Phase 0 re-audit: compileall passed, ruff passed, pytest passed with 118 tests, and API smoke returned `/health` 200, `/admin/login` 200, and unauthenticated `/api/machines` 401.

## Strict Prompt Completion Slice (2026-06-01)

- Production machine listing hides fake/demo machine rows unless demo mode is explicitly requested.
- `seed_admin()` and `main.py` no longer seed/start fake demo machines by default.
- Application whitelist is now Zalo, Discord, VSCode, Chrome, Notepad.
- API application start/stop requires consent and rejects non-whitelisted/raw command starts.
- Added `apps.agent.remote_files` for existing `X:\Remote` roots with path escape protections.
- Added API remote file list/download commands with consent gates.
- Added webcam device enumeration and API-selected `device_id` start.
- Added native Tkinter consent popup path with Yes/No/15-second timeout and deny-on-failure behavior.

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
- Follow-up UI guard: machine commands now stop client-side with clear messages when control has not been claimed, webcam consent is unchecked, or uploads fail validation; file upload dispatch now uses the real `/api/machines/{id}/file-dispatch` command path.
- Follow-up input guard: Keyboard Demo input now waits for controller-role acknowledgment before sending key codes, and global page keyboard forwarding is disabled so only typed keys inside the demo box are sent.
- Follow-up power guard: lock/cancel are confirmed and audited without requiring a reason, while restart/shutdown keep the minimum reason requirement.

## Defense Readiness Pass (2026-05-30)

- Added strict relay machine-secret verification through the internal API; unknown, empty, wrong, and disabled machine credentials are rejected and audited without leaking secrets.
- Added durable consent request, decision, policy models and service helpers.
- Added consent request/decision API routes and wired sensitive UI actions to request local agent approval before execution.
- Screen streaming no longer starts immediately after agent websocket auth; the agent starts frames only after a `screen_start` command and stops on `screen_stop`.
- Added machine-scoped grant enforcement for teacher access to machine control, file, webcam, power, audit, and view actions.
- Changed root `client.py` default to demo-safe mode and added explicit lab-real confirmation helpers.
- Added first-class allowlisted process start route and agent command handling.
- Added `/health`, lab-real launcher, submission cleanup scripts, and final defense docs.

## Verification

- `python -m compileall .`: passed.
- `python -m pytest -q`: passed, 94 tests.
- `ruff check .`: passed.
- Smoke: `/health` returned 200, `/admin/login` returned 200, `/api/machines` without auth returned 401.
