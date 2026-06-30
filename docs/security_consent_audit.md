# Security and consent audit

Date: 2026-05-30

## 2026-06-23 loop engineering update

The consent policy is now exact payload-bound. Consent requests store a canonical command payload hash, and execution checks recompute that hash before allowing the command. An approval for one app, file path, process PID, webcam device, keylogger session, or power payload cannot be reused for another payload.

The sensitive command set now includes `WEBCAM_ENUMERATE` and `KEYLOGGER_EXPORT` in addition to start/stop/control actions. File list/download, webcam enumerate/start/stop, keylogger start/stop/export, app start/stop, process kill, screen, and power routes all use the exact payload check.

The Keylogger Lab Module is allowed only as a visible lab module: no capture before local Yes, timeout means deny, no hidden persistence, short TTL, in-memory storage by default, separate export consent, and sensitive-window redaction.

Remaining security blocker: physical Windows validation evidence is not present. The current score is capped at 96/100 until `artifacts/physical_validation/` contains the required screenshots and notes.

## 2026-06-13 update

The consent policy now explicitly includes:

- `APPLICATION_START`
- `APPLICATION_STOP`
- `PROCESS_KILL`
- `SCREENSHOT`
- `LIVE_SCREEN`
- `KEY_INPUT`
- `KEYLOGGER_START`
- `KEYLOGGER_STOP`
- `FILE_LIST`
- `FILE_DOWNLOAD`
- `WEBCAM_START`
- `WEBCAM_STOP`
- `POWER_RESTART`
- `POWER_SHUTDOWN`

This pass closed two route gaps:

- Process stop now calls `require_active_consent()` with `PROCESS_KILL` before returning the relay command.
- Webcam stop now calls `require_active_consent()` with `WEBCAM_STOP` and rejects requests without the local consent flag.

The browser UI now creates and forwards local consent requests for process stop and webcam stop before sending those commands. Regression coverage was added for both paths, and the full verification gate passed with 120 tests.

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
- `KEYLOGGER_STOP`
- `PROCESS_KILL`
- `FILE_LIST`
- `FILE_DOWNLOAD`
- `WEBCAM_START`
- `WEBCAM_STOP`
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
- Demo mode is development-only and requires `TELEPC_ALLOW_DEMO=true`.
