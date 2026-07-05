# TelePC invariant registry

Automated status reflects the 2026-07-04 run with 214 passing tests. `MANUAL` items require the physical Windows evidence package.

## Security invariants

| ID | Invariant | Code area | Test/evidence | Status |
|---|---|---|---|---|
| SEC-001 | Sensitive actions require an authenticated user. | API dependencies | auth, grant, keylogger tests | PASS |
| SEC-002 | Sensitive actions require role plus machine grant/admin. | `deps.py` | `test_machine_grants.py` | PASS |
| SEC-003 | Execution requires local agent popup approval. | consent relay flow | agent/relay consent tests | PASS |
| SEC-004 | Consent binds machine, requester, command ID, action, and payload hash. | consent service/relay | exact-payload and all-action tests | PASS |
| SEC-005 | Popup timeout denies. | agent consent | `test_agent_consent.py` | PASS |
| SEC-006 | Denied consent never executes. | consent service | consent workflow tests | PASS |
| SEC-007 | Expired consent never executes. | consent service | consent/race tests | PASS |
| SEC-008 | Payload or command-ID mismatch never executes. | consent service/relay | consent fuzz tests | PASS |
| SEC-009 | Machine secrets are not logged. | redaction/auth | relay/audit security tests | PASS |
| SEC-010 | Credential fields are redacted and audit input is bounded. | audit/redaction | `test_audit_security.py` | PASS |

## Runtime invariants

| ID | Invariant | Code area | Test/evidence | Status |
|---|---|---|---|---|
| RUN-001 | Production hides fake/demo machines. | machine service/relay | real-machine tests | PASS |
| RUN-002 | Client and EXE default to real mode. | client/config | client/packaging tests | PASS |
| RUN-003 | Demo requires explicit environment plus flag. | client/relay | client mode tests | PASS |
| RUN-004 | Offline agent cannot receive a command. | relay registry | WS integration tests | PASS |
| RUN-005 | Wrong/empty/unknown secret cannot connect. | relay auth | relay auth tests | PASS |
| RUN-006 | Disabled machine cannot connect. | machine auth | relay auth tests | PASS |
| RUN-007 | Results correlate by command session ID. | browser WS client | `test_relay_routing.py` | PASS |
| RUN-008 | Stale/out-of-order results are not assigned FIFO. | browser WS client | `test_relay_routing.py` | PASS |
| RUN-009 | Reconnect closes and replaces the stale agent socket. | relay registry | `test_race_conditions.py` | PASS |
| RUN-010 | Heartbeat timeout transitions stale/offline. | relay monitor | reconnect/status tests | PASS |

## Module invariants

| ID range | Invariant group | Test/evidence | Status |
|---|---|---|---|
| APP-001..007 | Exact five-app whitelist; missing apps remain visible; raw/confusable keys rejected; stop/CPU match only app executables. | application unit/API/fuzz tests | PASS |
| PROC-001..005 | Separate process list; invalid/critical/PID-reused kills rejected; exact consent required; disappearing processes/NaN safe. | process tests | PASS |
| FILE-001..009 | Existing discovered `X:\Remote` only; traversal, absolute, UNC, symlink/junction escape, reserved names, oversize reads, and free UI paths blocked. | file, Windows-path, UI contract tests | PASS |
| CAM-001..005 | Agent devices rendered; no static fallback; empty state; selected device used; no pre-consent frame. | webcam API/UI/provider tests | PASS |
| KEY-001..009 | No startup capture; exact consent; deny/timeout; independent TTL; one active session; stop; mocked tests; redaction; memory-only storage. | keylogger/race tests | PASS |

## UI and packaging invariants

| ID | Invariant | Test/evidence | Status |
|---|---|---|---|
| UI-001 | Correlated action result exposes success/error; Keylogger waits for agent and expires locally. | relay/keylogger UI contracts | PASS |
| UI-002 | Disallowed camera/actions are disabled or rejected server-side. | webcam and permission tests | PASS |
| UI-003 | Errors are surfaced and pending promises reject on disconnect. | WS client contract | PASS |
| UI-004 | Page is machine-bound and stale command results require matching session ID. | routing/UI tests | PASS |
| PKG-001 | `TelePCClient.exe` builds. | final build log | PASS |
| PKG-002 | EXE default is real. | packaging/client tests | PASS |
| PKG-003 | EXE help works. | final help log | PASS |
| PKG-004 | EXE does not require fake runtime. | packaging test | PASS |

## Physical invariants

| ID | Invariant | Evidence | Status |
|---|---|---|---|
| PHY-001 | Real connected Windows client and relay behavior. | `01_connected_machine.png`, notes | MANUAL/MISSING |
| PHY-002 | Real Yes/No/15-second popup focus and timeout. | `02_consent_popup.png`, notes | MANUAL/MISSING |
| PHY-003 | Real app/file/webcam/Keylogger/audit behavior. | remaining six required artifacts | MANUAL/MISSING |
