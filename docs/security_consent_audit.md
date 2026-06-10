# Security and consent audit

Date: 2026-05-30

## Security posture at start

- Safe demo intent is documented.
- Real input and real power providers are environment-gated, but root `client.py` defaults to `--mode real`.
- Relay machine authentication is weak until it verifies machine secrets against the API.
- Current consent is not durable; sensitive routes use boolean request fields and audit logs.
- Agent screen streaming starts immediately after websocket connection and must be command-gated.
- File sandbox checks exist in API and agent, but route-level denial audits need review.

## Consent policy target

Sensitive commands must be blocked unless a matching approved, unexpired consent record exists for machine, command type, and requester:

- `SCREENSHOT`
- `LIVE_SCREEN`
- `KEY_INPUT`
- `KEYLOGGER_START`
- `FILE_DOWNLOAD`
- `WEBCAM_START`
- `POWER_RESTART`
- `POWER_SHUTDOWN`

Denied, pending, expired, and mismatched consent must block execution and write audit logs.

## Final security result

- `ConsentRequest`, `ConsentDecision`, and `ConsentPolicy` models exist.
- Sensitive API routes call `require_active_consent()` before execution.
- The browser creates a consent request and forwards it through the relay to the visible agent prompt.
- The agent defaults to denial on EOF/timeout-style failures.
- Consent decisions are written back to the API and audited.
- Relay auth rejects unknown, disabled, empty, and wrong machine secrets.
- Real input/power remain disabled by default and require lab-real confirmation.
