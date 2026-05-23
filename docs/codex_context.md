# Codex Context

Repo: `project1-remotedesktop`

Purpose: TelePC lab remote desktop control system with browser admin, relay proxy, and consent-visible client agent.

Current implementation:

- FastAPI API/admin app under `apps/api`.
- Async SQLAlchemy models and SQLite default DB.
- WebSocket relay under `apps/relay`.
- Fake/real-capable agent under `apps/agent`; fake mode is the demo-safe default.
- Shared protocol, enums, redaction, and crypto helpers under `shared`.
- Pytest suite covers auth, ACL, protocol, sandbox, audit redaction, process command policy, enrollment, machine listing, session lock, audit order, file/job flow, and relay forwarding.

Safety decisions:

- No stealth, persistence, AV bypass, or credential collection.
- Key input captures metadata only; `keystroke_content` is redacted.
- File writes are confined to `sandbox_root/<machine_id>/<job_id>/`.
- Job runners and application starts use allowlists.

