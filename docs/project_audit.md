# TelePC project audit

Date: 2026-05-30

## Starting audit summary

This audit begins from the requested known findings plus local code inspection.

| Finding | Status at start | Required fix |
|---|---|---|
| Relay machine secret check accepts any non-empty secret | Confirmed in `apps/relay/auth.py`. | Verify against registered `machine_secrets` and audit attempts. |
| Agent sends screen frames immediately after connection | Confirmed in `apps/agent/ws_client.py`. | Stream only after approved command and active consent. |
| Consent is not a real approval workflow | Confirmed; route bodies use boolean `consent`. | Add consent request, decision, expiry, and audit. |
| Keylogger is not lab-only approved | Current implementation is scoped Keyboard Demo metadata/input forwarding. | Keep ethical Keyboard Demo unless safe lab capture is explicitly justified. |
| Start Process first-class feature missing | Application start exists; process start route is not first-class. | Add safe allowlisted process start path or document app-start equivalence. |
| Student and Agent actors incomplete | Roles include admin, teacher, auditor; agent identity is websocket-only. | Make actor model explicit in docs and enforcement. |
| MachineGrant exists but is not enforced per machine | Confirmed. | Enforce grants on machine-scoped actions. |
| Ruff fails | Unknown until baseline run. | Run and fix. |
| `/health` missing | Confirmed. | Add health endpoint. |
| Zip contains local artifacts | Cleanup scripts missing. | Add submission cleanup scripts and checklist. |

## Initial risk ranking

1. Relay machine authentication.
2. Durable consent and screen/webcam/file/power gates.
3. Machine-scoped authorization.
4. Real-mode launch safety.
5. Verification and submission packaging.

## Final audit result

- Relay machine authentication is fixed and covered by `tests/test_relay_auth.py`.
- Durable consent request/decision/expiry is implemented and covered by `tests/test_consent_workflow.py`.
- Visible local agent consent prompt is covered by `tests/test_agent_consent.py`.
- Machine grants are enforced for non-admin machine-scoped actions and covered by `tests/test_machine_grants.py`.
- Root client defaults to demo-safe mode and lab-real requires explicit confirmation, covered by `tests/test_client_real_mode.py`.
- Agent screen frames no longer stream immediately after websocket auth.
- Verification passed: compileall, pytest, ruff, and API smoke.
