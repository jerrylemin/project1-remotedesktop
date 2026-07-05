# Minimal refactor plan

## Goal

Reduce dead code, pass-through wrappers, and unused configuration without changing TelePC behavior, public HTTP/WebSocket contracts, security, consent, audit, or tests.

## Baseline

Date: 2026-07-05

| Metric | Value |
|---|---:|
| Python files (`apps`, `scripts`) | 73 |
| JavaScript files | 6 |
| Test files | 63 |
| Total Python/JavaScript/test lines | 7,271 |
| Compile | PASS |
| Ruff | PASS |
| Pytest | PASS, 221 tests |

No `src/` directory or current Graphify report exists. Source lives under `apps/`; the mandatory audit report exists under `artifacts/audit/`.

## Findings

| Finding | File | Current issue | Minimal fix | Risk | Test needed |
|---|---|---|---|---|---|
| Pass-through input module | `apps/agent/input_demo.py` | Wraps `input_provider.handle_input_event` without adding behavior | Import the real function directly and delete the wrapper | Low | Existing input/provider tests |
| Dead relay helper | `apps/relay/session_manager.py` | No imports or callers | Delete file | Low | Full suite |
| Dead agent audit client | `apps/agent/audit_client.py` | No imports or callers; active audit path is relay/API | Delete file | Low | Audit and relay tests |
| Dead enrollment client | `apps/agent/enrollment.py` | No imports or callers; active enrollment path is `/api/agents/enroll` | Delete file | Low | Enrollment integration tests |
| Unused settings | `apps/agent/config.py` | `enable_real_input` and `enable_real_power` are never read | Delete two fields; providers retain environment gates | Low | Real client/input/power tests |
| Pass-through file aliases | `apps/agent/remote_files.py` | Two aliases only convert types and call the real functions | Use the real functions from `commands.py`; delete aliases | Low | File whitelist and command tests |
| Repeated sensitive-route flow | `apps/api/routers/machines.py` | Many routes repeat access, consent, audit, commit | Keep existing small helpers; a generic action framework would add parameters and hide security decisions | High | Not selected |
| Long command/UI dispatchers | `apps/agent/commands.py`, `machine_detail.js` | Large but each branch maps directly to a user-visible action | Keep explicit branches; splitting would add indirection without deleting behavior | Medium | Not selected |
| Explicit demo/fake runtime | demo scripts and fake providers | Looks removable but is required for opt-in demos and tests | Keep behind existing opt-in gates | High | Not selected |

## Patch loop

### Patch 1 — Remove proven dead modules and unused settings

- Delete only files with zero repo callers.
- Replace the one-line input wrapper with a direct import.
- Remove the two unused settings fields.
- Run focused input, client, relay, audit, and enrollment tests; then full verification.

Result: PASS. Removed four modules and two unused settings fields. Focused tests: 27 passed. Full verification: compile PASS, Ruff PASS, 221 tests PASS.

### Patch 2 — Remove remote-file pass-through aliases

- Import the existing core file functions directly in `commands.py`.
- Preserve filename and payload behavior.
- Run focused file whitelist/command tests; then full verification.

Result: PASS. Removed two aliases and used the existing core functions directly. Focused tests: 39 passed. Full verification: compile PASS, Ruff PASS, 221 tests PASS.

`@ponytail-review` result: Lean already. Ship. No additional abstraction or wrapper was introduced.

## Non-negotiable gates

Auth/RBAC, machine secret verification, local 15-second consent, exact payload binding, application/process separation, file boundaries, webcam enumeration, visible TTL-bound Keylogger Lab Module, audit lifecycle, real-mode EXE default, and explicit-only demo mode remain unchanged.
