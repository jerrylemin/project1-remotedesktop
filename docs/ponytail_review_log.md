# Ponytail review log

| Review pass | Concern | Evidence checked | Result | Patch needed |
| ----------- | ------- | ---------------- | ------ | ------------ |
| LOOP 0 | Avoid broad rewrites before plan. | Baseline audit and green tests. | Use narrow patches against existing services/routes/JS. | No source patch yet. |
| LOOP 2 | `@ponytail-review apps/agent/remote_files.py apps/api/routers/machines.py apps/api/static/js/machine_detail.js tests/test_file_whitelist.py` | File whitelist diff and focused tests. | Lean enough; reuses existing relay/API command flow and adds no dependency. | No. |
| LOOP 3 | `@ponytail-review apps/agent apps/api tests/test_keylogger_lab_module.py` | Keylogger lab module and exact-consent tests. | Keep in-memory only; no DB table or persistence layer needed for current gate. | No. |
| LOOP 4 | `@ponytail-review apps/api/services/consent.py apps/api/routers/machines.py tests/test_consent_exact_payload.py` | Payload hash binding diff. | Reuses existing ConsentRequest flow; no separate CommandPayloadBinding table needed. | No. |
| LOOP 5 | `@ponytail-review apps/api/static/js/machine_detail.js apps/api/templates/machine_detail.html tests/test_webcam_ui_contract.py` | Webcam device UI diff. | Lean already; awaited relay result replaces static fallback without new UI framework. | No. |
| LOOP 6 | `@ponytail-review client.py apps/agent/config.py apps/agent/providers.py tests/test_client_real_mode.py` | Demo/default runtime diff. | Keep fake providers only for explicit dev/test mode; production default is now real. | No. |
| LOOP 7 | `@ponytail-review docs/loop_scoreboard.md artifacts/loop` | Verification artifacts and score doc. | Keep only command evidence and cap note; no extra audit framework. | No. |
| LOOP 8 | Physical validation package. | `scripts/run_physical_lab_validation.ps1`, checklist, evidence README. | Script is prompt-only and non-destructive; no automation of risky actions. | No. |
| LOOP 10.1 | One reason this might not deserve 100: physical evidence could be missing. | `artifacts/physical_validation/README.md` and required screenshots. | Real blocker confirmed; final score capped at 96/100. | Docs only. |
| LOOP 10.2 | One reason this might not deserve 100: dead Keyboard Demo browser path might remain. | `rg "sendKeyboardDemoEvent|keyboard-input" apps tests`. | Dead JS helper and orphan CSS selector were removed. | Yes, completed. |
| LOOP 10.3 | One reason this might not deserve 100: static webcam fallback might remain. | `rg "Camera 0" apps/api/static/js apps/api/templates tests`. | No production fallback remains; test fixtures/documented prototype references only. | No. |
