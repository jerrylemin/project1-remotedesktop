# Security Model

Authentication:

- Admin login returns signed bearer token.
- Agent enrollment uses a one-time enroll token and receives a machine secret.

Authorization:

- Roles: `admin`, `teacher`, `auditor`.
- Machine grants model per-machine ACL fields: view, control, file, webcam, power, audit.
- HTTP endpoints enforce role permissions.
- Relay enforces controller lock before forwarding command/input/file messages.

Consent and safety:

- Agent prints a visible consent/control banner.
- Fake mode is default for demo/test.
- Key input stores metadata only.
- Dangerous actions require `CONFIRM` in UI and are intended to be audited.

Audit and redaction:

- Audit metadata is recursively redacted for `password`, `token`, `session_raw_id`, `keystroke_content`, `cookie`, `private_key`, and `file_content`.

