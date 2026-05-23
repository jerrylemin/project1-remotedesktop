# Relay Protocol

All WebSocket messages use this envelope:

```json
{
  "type": "heartbeat|auth|subscribe_machine|frame|command|command_result|input_event|file_dispatch|job_status|audit_event|ack|error",
  "msg_id": "uuid",
  "machine_id": "uuid-or-null",
  "session_id": "uuid-or-null",
  "ts": "ISO8601 UTC",
  "payload": {}
}
```

Flows:

- Agent connects to `/ws/agent`, sends `auth` with `machine_id` and `machine_secret`.
- Admin connects to `/ws/admin`, sends `auth` with short-lived `ws_ticket`.
- Relay validates the ticket through `POST /internal/ws-ticket/validate` using `INTERNAL_API_SECRET`.
- Admin sends `subscribe_machine` with `control: true` to claim controller lock or `false` to observe.
- Agent sends `frame`; relay forwards to all subscribers for that machine.
- Controller sends `command`, `input_event`, or `file_dispatch`; relay forwards only if controller lock is held.
- Agent sends `command_result` or `job_status`; relay forwards to subscribers.
- Agent sends `heartbeat`; relay updates DB status and `last_seen`.
- Relay status monitor marks machines `stale` and `offline` after configured timeouts.
