# API

Auth:

- `POST /auth/login`: JSON `{username, password}` returns bearer token and sets session cookie.
- `POST /auth/logout`: clears session cookie.
- `POST /api/ws-ticket`: returns a short-lived single-use WebSocket ticket from the HttpOnly session.

Admin pages:

- `GET /admin/login`
- `GET /admin/dashboard`
- `GET /admin/machines`
- `GET /admin/machines/{machine_id}`

Machines:

- `GET /api/machines`
- `GET /api/machines/{machine_id}`
- `POST /api/enroll-tokens`
- `POST /api/agents/enroll`

Sessions:

- `POST /api/sessions`
- `POST /api/sessions/{session_id}/claim`
- `POST /api/sessions/{session_id}/release`

Audit:

- `GET /api/machines/{machine_id}/audit`
- Optional filters: `event_type`, `actor_type`, `start`, `end`

Files and jobs:

- `POST /api/files/upload`
- `POST /api/files/{artifact_id}/dispatch`
- `GET /api/files/machines/{machine_id}`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`
- `GET /api/jobs/machines/{machine_id}/history`

Internal relay/API endpoints:

- `POST /internal/ws-ticket/validate`
- `POST /internal/audit`
- `POST /internal/machines/status`
- These require `X-TelePC-Internal-Secret`.

All admin REST endpoints require bearer token or session cookie.
