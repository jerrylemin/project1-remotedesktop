# TelePC requirement matrix

Date: 2026-05-30

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
| Keylogger lab module | INTENTIONAL DEVIATION | Project currently implements scoped Keyboard Demo, not silent/global key capture. |
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
| Keylogger or ethical Keyboard Demo | PASS | Scoped Keyboard Demo with key-code-only forwarding. |
| Download file | PASS | Sandbox traversal and symlink checks. |
| Start, stop webcam | PASS | Durable consent plus webcam tests. |
| Reset, shutdown | PASS | Consent/RBAC/real-mode tests. |
| Authentication | PASS | Login/session tests. |
| Authorization | PASS | `tests/test_machine_grants.py`. |
| Consent | PASS | `tests/test_consent_workflow.py`, `tests/test_agent_consent.py`. |
| Audit logging | PASS | Auth, consent, command audit paths. |
| Demo readiness | PASS | Compile, pytest, ruff, smoke passed. |
