# Data Model

Implemented tables:

- `users`: admin accounts and login status.
- `roles`, `user_roles`: role permission mapping.
- `machines`: enrolled machines and online status.
- `machine_secrets`: hashed machine secrets.
- `machine_grants`: per-user machine ACL fields.
- `relay_nodes`: relay heartbeat records.
- `control_sessions`, `session_participants`: controller/observer sessions.
- `artifacts`: uploaded files stored outside static files.
- `sandbox_files`: machine/job sandbox dispatch records.
- `jobs`: sandbox job request/result records.
- `audit_events`: per-machine audit records with redacted metadata.
- `enroll_tokens`: one-time enrollment tokens.

SQLite is the default; PostgreSQL can be used by setting `DATABASE_URL`.

