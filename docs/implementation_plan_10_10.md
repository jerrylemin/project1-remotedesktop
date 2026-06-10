# TelePC 10/10 implementation plan

Date: 2026-05-30

## Strict prompt continuation, 2026-06-01

Phase 0 was rerun under the stricter pasted prompt.

- `~/.codex/AGENTS.md` and `~/.codex/config.toml` were read.
- Local skills used: `repo-audit`, `graphify-workflow`, `tdd`, and `docs-memory-maintainer`.
- Graphify was refreshed with `graphify update .`; output: 1111 nodes, 3280 edges, 89 communities.
- Baseline environment: Python 3.11.9, pip 26.1.1.
- Dependency install check: `python -m pip install -r requirements.txt` reported requirements already satisfied.
- Verification: `python -m compileall .` passed, `ruff check .` passed, `python -m pytest -q` passed with 98 tests after packaging coverage was added.
- API smoke on port 8765 passed: `/health` 200, `/admin/login` 200, and unauthenticated `/api/machines` 401.

Completion slice decisions:

| Condition | Current state | Decision |
|---|---|---|
| Fake/demo agents visible by default | Fixed. | Production-safe default hides demo machines and only starts fake agents with `--demo-agents`. |
| Required client EXE packaging | Fixed. | `dist\TelePCClient.exe` rebuilt and `--help` smoke passed. |
| Strict app whitelist mismatch | Fixed. | Agent whitelist and API control path now use Zalo, Discord, VSCode, Chrome, Notepad. |
| File whitelist mismatch | Fixed at contract/agent level. | Added `X:\Remote` discovery/list/download module and API relay commands. |
| Webcam selection missing | Fixed at contract/agent level. | Added device enumeration and required `device_id` for start. |
| Native timed popup missing | Fixed at agent level. | Added Tkinter popup with Yes, No, 15-second timeout, and deny-on-error. |
| Global keylogger request | Intentionally not implemented as stealth/global capture. | Project keeps scoped Keyboard Demo to avoid credential collection. |

Updated decision table:

| Condition | Current state | Decision |
|---|---|---|
| Fake/demo agents exist | Still present for demos and tests. | Keep for explicit demo/test only; remove from production startup/UI in a later slice. |
| Required client EXE packaging missing | No `build_client_exe.ps1` existed at start of 2026-06-01 pass. | Added packaging script and tests. |
| Strict app whitelist mismatch | Current allowlist is not the required five-app list. | Pending implementation. |
| File whitelist mismatch | Current file flow is sandbox artifact transfer. | Pending `X:\Remote` controlled-machine discovery/list/download module. |
| Webcam selection missing | Current real webcam provider uses index 0. | Pending device enumeration and device-id selection. |
| Native timed popup missing | Current agent prompt uses console input and API TTL. | Pending native Windows popup with timeout. |

## Starting context loaded

- Read global Codex agreements from `~/.codex/AGENTS.md`.
- Read Codex config from `~/.codex/config.toml`; Superpowers, GitHub, and Gmail plugins are enabled.
- Available Codex subagents found under `~/.codex/agents`: `docs_memory_maintainer`, `graphify_operator`, `repo_auditor`, `security_reviewer`, and `test_runner`.
- Superpowers workflow loaded from the installed plugin cache.
- Local `AGENTS.md`, `README.md`, `docs/codex_context.md`, `docs/project_structure.md`, `docs/session_handoff.md`, and `docs/feature_progress.md` were read.
- Graphify wrapper was available and run with `graphify.exe update . --no-cluster`; output graph has 966 nodes and 3294 edges in `graphify-out/graph.json`.
- Prior requested audit files were missing at start: `docs/project_audit.md`, `docs/telepc_requirement_matrix.md`, `docs/final_compliance_report.md`, `docs/defense_readiness_checklist.md`, and `docs/security_consent_audit.md`.

## Baseline finding decision table

| Condition | Observed starting state | Decision |
|---|---|---|
| Security-critical guardrail missing | Relay `validate_agent_secret()` accepts any non-empty machine id and secret. | Fix before feature polish. |
| Consent workflow is fake | API routes accept boolean consent fields; no durable consent request/decision model exists. | Add durable request/approval/denial/expiry flow before sensitive commands. |
| Agent auth is weak | Relay does not verify against registered machine secrets. | Add internal API verification and relay contract tests. |
| MachineGrant exists but is not enforced | Routes use broad role permissions only. | Add machine-scoped authorization helper and route enforcement. |
| Agent sends screen frames immediately | `apps/agent/ws_client.py` starts `send_frames()` immediately after auth. | Change to command-gated streaming only after approved start. |
| Real mode unsafe default | Root `client.py` defaults to `--mode real`. | Make demo mode default and add explicit lab-real confirmation path. |
| `/health` missing | API app has no explicit health endpoint. | Add simple unauthenticated health endpoint. |
| Submission cleanup missing | Cleanup scripts are absent. | Add PowerShell and shell cleanup/zip scripts. |

## Likely files to change

- `apps/api/models.py`
- `apps/api/schemas.py`
- `apps/api/deps.py`
- `apps/api/services/machine.py`
- `apps/api/services/consent.py`
- `apps/api/routers/internal.py`
- `apps/api/routers/machines.py`
- `apps/api/main.py`
- `apps/relay/api_client.py`
- `apps/relay/auth.py`
- `apps/relay/router.py`
- `apps/agent/ws_client.py`
- `apps/agent/consent.py`
- `client.py`
- `scripts/run_lab_real_client.ps1`
- `scripts/prepare_submission.ps1`
- `scripts/prepare_submission.sh`
- `tests/test_relay_auth.py`
- `tests/test_machine_grants.py`
- `tests/test_consent_workflow.py`
- `tests/test_agent_consent.py`
- `tests/test_client_real_mode.py`
- Required docs and handoff files under `docs/`.

## Verification plan

Run the smallest targeted tests after each security slice, then finish with:

```bash
python -m compileall .
python -m pytest -q
ruff check .
```

Smoke API if the app starts:

```bash
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
curl -i http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/admin/login
curl -i http://127.0.0.1:8000/api/machines
```

## Final execution record

Implementation completed on 2026-05-30.

Security decisions applied:

- Relay auth must verify against registered `MachineSecret`; demo machines are seeded with `fake-secret` for fake-agent demos.
- Non-admin users must have `MachineGrant` rows for machine-scoped actions.
- Sensitive commands require durable consent approval. The UI requests consent, forwards it to the visible agent prompt through relay, records the decision, and then submits the sensitive command.
- Plain `python client.py` is demo-safe. Lab-real mode requires `TELEPC_LAB_AUTHORIZED`.
- Tests and pytest execution cannot execute real power commands even if the surrounding shell has real-mode env vars set.

Verification:

| Command | Result |
|---|---|
| `python -m compileall .` | Passed |
| `python -m pytest -q` | Passed, 94 tests |
| `ruff check .` | Passed |
| `py -3.12 -m pytest tests/test_relay_auth.py -q` | Passed |
| `py -3.12 -m pytest tests/test_consent_workflow.py -q` | Passed |
| `py -3.12 -m pytest tests/test_machine_grants.py -q` | Passed |
| `py -3.12 -m pytest tests/test_client_real_mode.py -q` | Passed |
| `/health` smoke | 200 OK |
| `/admin/login` smoke | 200 OK |
| `/api/machines` unauth smoke | 401 Unauthorized |
