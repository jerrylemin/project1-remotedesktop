# Audit Logs

Audit records are stored in `audit_events` and can be queried per machine using:

```text
GET /api/machines/{machine_id}/audit
```

Event metadata is redacted before persistence. Sensitive fields:

- `password`
- `token`
- `session_raw_id`
- `keystroke_content`
- `cookie`
- `private_key`
- `file_content`

Core event types include login/logout, enrollment, online/stale/offline status, session lifecycle, screenshot, application/process commands, sandbox files/jobs, webcam, power requests, auth failures, ACL denial, and command failures.

