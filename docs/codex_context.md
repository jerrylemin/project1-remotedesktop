# Codex Context

Repo: `project1-remotedesktop`

Purpose: TelePC lab remote desktop control system with browser admin, relay proxy, and consent-visible client agent.

Current implementation:

- FastAPI API/admin app under `apps/api`.
- Async SQLAlchemy models and SQLite default DB.
- WebSocket relay under `apps/relay`.
- Real-capable consent-visible agent under `apps/agent`; demo/fake mode is explicit development/test opt-in only.
- Shared protocol, enums, redaction, and crypto helpers under `shared`.
- Pytest suite covers auth, ACL, protocol, sandbox, audit redaction, process command policy, enrollment, machine listing, session lock, audit order, file/job flow, and relay forwarding.

Safety decisions:

- No stealth, persistence, AV bypass, or credential collection.
- Keylogger Lab Module requires visible local consent, TTL, stop/export controls, and sensitive-window redaction.
- Remote file browsing is confined to discovered existing `X:\Remote` roots; sandbox file dispatch remains under `sandbox_root/<machine_id>/<job_id>/`.
- Job runners and application starts use allowlists.

