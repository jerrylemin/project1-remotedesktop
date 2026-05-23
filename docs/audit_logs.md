# Audit Logs

Audit records are stored in `audit_events` and can be queried per machine using:

```text
GET /api/machines/{machine_id}/audit
```

Filters:

- `event_type`
- `actor_type`
- `start`
- `end`

Relay audit bridge:

- Relay enqueues audit events in a background worker.
- The worker posts to `POST /internal/audit` with `INTERNAL_API_SECRET`.
- Failures are logged server-side and do not crash WebSocket sessions.

Machine status transitions:

- Agent connect: `online` and `agent_online`.
- Heartbeat: updates `last_seen` without repeated audit spam.
- Heartbeat timeout: `stale` and `agent_stale`.
- Disconnect/offline timeout: `offline` and `agent_offline`.
- Audit is written only when status changes.

Event metadata is redacted before persistence. Sensitive fields:

- `password`
- `token`
- `session_raw_id`
- `keystroke_content`
- `cookie`
- `private_key`
- `file_content`

Core event types include login/logout, enrollment, online/stale/offline status, session lifecycle, screenshot, application/process commands, sandbox files/jobs, webcam, power requests, auth failures, ACL denial, and command failures.
