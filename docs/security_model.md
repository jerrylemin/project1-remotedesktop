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
- Fake mode is default for demo/test.
- Key input stores metadata only.
- Dangerous actions require `CONFIRM` in UI and are intended to be audited.
- Real agent providers have fake and safe fallback behavior. Missing optional dependencies return clear command errors instead of crashing the agent.

Audit and redaction:

- Audit metadata is recursively redacted for `password`, `token`, `session_raw_id`, `keystroke_content`, `cookie`, `private_key`, and `file_content`.
