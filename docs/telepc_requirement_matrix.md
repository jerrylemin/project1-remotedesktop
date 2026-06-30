# TelePC requirement matrix

Date: 2026-05-30

## Loop engineering update, 2026-06-23

| Requirement | Current status | Evidence |
|---|---|---|
| Real machines only | PASS | `client.py` defaults to real; demo requires `--mode demo` and `TELEPC_ALLOW_DEMO=true`; relay rejects demo identities unless explicitly allowed. |
| Mandatory WebSocket relay | PASS | Admin and agent paths use relay WebSockets. |
| Machine authentication | PASS | Relay verifies machine secret through API. |
| Controller authentication/authorization | PASS | Session auth, permissions, and machine grants are covered by tests. |
| Native consent popup with 15-second timeout | PASS | Agent popup path denies on No, timeout, EOF, or popup failure. |
| Exact payload-bound consent | PASS | `apps/api/services/consent.py` stores and verifies payload hashes. |
| Required app whitelist | PASS | Agent whitelist is Zalo, Discord, VSCode, Chrome, Notepad; API rejects non-whitelisted starts. |
| Process list/kill | PASS | Process listing and protected-process kill guards exist. |
| Keylogger lab module | PASS | Visible, consented, TTL-bound, in-memory Keylogger Lab Module; no stealth/persistence. |
| `X:\Remote` file whitelist | PASS | Agent only accepts discovered existing roots and blocks traversal/UNC/absolute overrides/symlink escapes. |
| Webcam device selection | PASS | UI awaits and renders agent-returned devices; selected `device_id` is sent. |
| One-file Windows client EXE | PASS | `scripts/build_client_exe.ps1` built `dist\TelePCClient.exe`; `Test-Path` returned True. |
| Audit logging | PASS | Consent/action audit paths covered by tests. |
| Physical Windows validation | PARTIAL | Required screenshots and `validation_notes.md` are still missing under `artifacts/physical_validation/`. |

## Strict consent update, 2026-06-13

| Requirement | Current status | Evidence |
|---|---|---|
| Process kill requires local consent | PASS | `apps/api/routers/machines.py` now requires `PROCESS_KILL`; UI calls `requestLocalConsent("PROCESS_KILL", ...)`; `tests/integration/test_teacher_ui_routes.py::test_process_stop_requires_approved_consent`. |
| Webcam stop requires local consent | PASS | `apps/api/routers/machines.py` now requires `WEBCAM_STOP`; UI calls `requestLocalConsent("WEBCAM_STOP", ...)`; `tests/test_webcam_devices_api.py::test_webcam_stop_requires_approved_consent`. |
| Production UI avoids fake-agent empty-state instructions | PASS | Dashboard and machines page now instruct admins to enroll/run `TelePCClient.exe`, not fake demo agents. |
| Full automated gate | PASS | `python -m compileall .`, `ruff check .`, `python -m pytest -q` with 120 tests, `.\scripts\build_client_exe.ps1`, EXE `--help`, and HTTP smoke all passed. |

## Strict prompt delta, 2026-06-01

| Requirement | Current status | Evidence |
|---|---|---|
| Real machines only | PASS | Fake/demo machines are hidden by default; demo seeding requires explicit opt-in. |
| Mandatory WebSocket relay | PASS | Admin and agent paths use relay WebSockets. |
| Machine authentication | PASS | Relay verifies machine secret through API. |
| Controller authentication/authorization | PASS | Session auth, permissions, and machine grants are covered by tests. |
| Native consent popup with 15-second timeout | PASS | Agent has Tkinter popup path with Yes, No, topmost window, timeout denial, and failure denial. |
| Required app whitelist | PASS | Agent whitelist is Zalo, Discord, VSCode, Chrome, Notepad; API rejects non-whitelisted starts. |
| Process list/kill | PASS | Process listing and protected-process kill guards exist. |
| Keylogger lab module | SUPERSEDED | See 2026-06-23 update; project now has a visible lab key capture module, not stealth/global capture. |
| `X:\Remote` file whitelist | PASS | `apps.agent.remote_files` discovers existing `X:\Remote` roots and blocks traversal/UNC/absolute escape. |
| Webcam device selection | PASS | Agent enumerates OpenCV devices; API requires `device_id` before webcam start. |
| One-file Windows client EXE | PASS | `scripts/build_client_exe.ps1` built `dist\TelePCClient.exe`; `--help` smoke passed. |
| Audit logging | PASS | Audit service and tests cover major action paths. |

| Requirement | Final status | Evidence |
|---|---|---|
| Client web app | PASS | Jinja UI smoke and route tests. |
| Controlled-machine server or agent | PASS | `client.py`, `apps/agent`, relay websocket tests. |
| Multi-machine control | PASS | Machine list/session/relay tests. |
| List, start, stop applications | PASS | API and agent tests. |
| List, start, stop processes | PASS | `tests/test_start_process_route.py`, process tests. |
| Screenshot | PASS | Consent gate and command-gated stream. |
| Keylogger lab module | PASS | Visible lab module with consent, TTL, stop/export controls, and sensitive-window redaction. |
| Download file | PASS | Sandbox traversal and symlink checks. |
| Start, stop webcam | PASS | Durable consent plus webcam tests. |
| Reset, shutdown | PASS | Consent/RBAC/real-mode tests. |
| Authentication | PASS | Login/session tests. |
| Authorization | PASS | `tests/test_machine_grants.py`. |
| Consent | PASS | `tests/test_consent_workflow.py`, `tests/test_agent_consent.py`. |
| Audit logging | PASS | Auth, consent, command audit paths. |
| Demo readiness | PASS | Compile, pytest, ruff, smoke passed. |
