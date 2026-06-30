# Loop scoreboard

Baseline score: 74/100.

Automated loop status: all source-code blockers have been patched and verified. Final score is capped at 96/100 until real Windows physical validation evidence is collected under `artifacts/physical_validation/`.

| Gate                                 | Points | Status | Evidence |
| ------------------------------------ | -----: | ------ | -------- |
| Real machines only                   |      8 | PASS | `client.py` defaults to real mode; demo requires `--mode demo` plus `TELEPC_ALLOW_DEMO=true`; relay rejects demo identities unless explicitly allowed. |
| WebSocket relay                      |      8 | PASS | `apps/relay/router.py`; smoke and full pytest pass. |
| Controller auth, owner, RBAC         |     10 | PASS | `apps/api/deps.py`, machine grants, route tests. |
| Machine auth and secret verification |      8 | PASS | `apps/relay/auth.py`, `/internal/machines/verify-secret`, relay auth tests. |
| Universal popup consent 15s          |     12 | PASS | `apps/agent/consent.py`; exact payload hashes in `apps/api/services/consent.py`; consent tests. |
| Application whitelist                |     10 | PASS | `apps/agent/app_manager.py`, app route tests. |
| Process module                       |      8 | PASS | `apps/agent/process_manager.py`, process route tests. |
| Keylogger lab module                 |      8 | PASS | `apps/agent/key_capture.py`, `/keylogger/*` routes, `tests/test_keylogger_lab_module.py`; physical evidence still required for final 100. |
| File whitelist                       |      8 | PASS | `apps/agent/remote_files.py`, remote file UI, `tests/test_file_whitelist.py`, `tests/test_remote_file_ui_contract.py`. |
| Webcam discovery and control         |      6 | PASS | Awaited device enumeration UI and route consent tests; physical device screenshots still required for final 100. |
| Audit logging                        |      6 | PASS | Consent/action audit assertions in focused tests and full suite. |
| Client one-file exe                  |      4 | PASS | `.\scripts\build_client_exe.ps1`; `Test-Path .\dist\TelePCClient.exe` returned `True`. |
| Tests, lint, compile, smoke          |      4 | PASS | `python -m compileall .`, `ruff check .`, `python -m pytest -q`, HTTP smoke all passed in LOOP 7. |
| README, report, defense docs         |      2 | PARTIAL | Docs updated with physical-validation package; final defense remains PARTIAL until evidence files exist. |
| Total                                |    100 | 96/100 capped | Automated implementation gates pass; missing external physical Windows evidence prevents 100/100. |

## Hard Gate Result

- No skipped compile: PASS.
- No skipped Ruff: PASS.
- No skipped pytest: PASS.
- No skipped smoke: PASS.
- No fake/demo production runtime default: PASS.
- No missing consent on listed control actions found in route coverage: PASS.
- No caller-supplied file root accepted by agent boundary: PASS.
- No static Camera 0 fallback: PASS.
- No DEMO_ONLY keylogger: PASS; replaced by visible, consented, timed, in-memory Keylogger Lab Module.
- No EXE default demo mode: PASS.
- Physical Windows evidence: MISSING, external blocker.
