# API

Auth:

- `POST /auth/login`: JSON `{username, password}` returns bearer token and sets session cookie.
- `POST /auth/logout`: clears session cookie.

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

Files and jobs:

- `POST /api/files/upload`
- `POST /api/files/{artifact_id}/dispatch`
- `POST /api/jobs`
- `GET /api/jobs/{job_id}`

All admin REST endpoints require bearer token or session cookie.

