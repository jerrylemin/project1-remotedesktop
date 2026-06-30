# Security Model

Authentication:

- Admin login returns signed bearer token.
- Browser login stores the admin session in an HttpOnly cookie.
- Browser WebSocket auth uses `POST /api/ws-ticket` to obtain a short-lived ticket, not `localStorage`.
- WS tickets are single-use, have a short TTL, and are validated by the relay through an API internal endpoint.
- Agent enrollment uses a one-time enroll token and receives a machine secret.
- Relay-to-API internal calls require `INTERNAL_API_SECRET`.

Authorization:

- Roles: `admin`, `teacher`, `auditor`.
- Machine grants model per-machine ACL fields: view, control, file, webcam, power, audit.
- HTTP endpoints enforce role permissions.
- Relay enforces controller lock before forwarding command/input/file messages.
- Relay rejects control subscriptions for WS tickets without `machines:control`.

Consent and safety:

- Agent prints a visible consent/control banner.
- Client real mode is the default. Fake/demo providers are for explicit development/test mode only.
- Consent is bound to the exact command payload hash before execution.
- The Keylogger Lab Module is visible, TTL-bound, in-memory by default, and requires local Yes before capture; export requires separate consent.
- Dangerous actions require local consent and are audited.
- Real agent providers have fake and safe fallback behavior. Missing optional dependencies return clear command errors instead of crashing the agent.

Audit and redaction:

- Audit metadata is recursively redacted for `password`, `token`, `session_raw_id`, `keystroke_content`, `cookie`, `private_key`, and `file_content`.
## Real-Machine Safety Model Update (2026-05-26)

- Consent-visible operation remains mandatory: the agent startup path prints the visible control banner, and demo mode requires explicit development opt-in.
- Admin pages use the same HttpOnly session cookie as API calls; unauthenticated page loads redirect to `/admin/login`, and underprivileged roles receive `403.html`.
- Controller lock is enforced in two places: the API owns the persistent `control_sessions` row, and the relay checks `/internal/control-session/{machine_id}` before forwarding protected commands.
- Observers may receive frames and results but command, input, and file-dispatch sends are rejected with `observer_only`.
- Real input is disabled unless `TELEPC_ENABLE_REAL_INPUT=true`; key capture is a separate visible lab module with consent, TTL, stop, and redaction.
- The browser no longer forwards global page keydown/keyup events.
- Remote file browsing is limited to discovered existing `X:\Remote` roots. The agent rejects arbitrary roots, dot segments, absolute paths, drive-letter overrides, UNC paths, nested unsafe filenames, symlink escapes, and SHA256 mismatches.
- Power actions build Windows commands but do not execute them unless `TELEPC_ENABLE_REAL_POWER=true`; all power actions require audit confirmation, and restart/shutdown require an audit reason.
- Audit metadata is redacted for password, token, secret, cookie, and authorization keys before storage.
