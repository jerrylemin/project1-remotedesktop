# Architecture

```mermaid
flowchart LR
  Admin["Browser Admin"] <-->|"WebSocket /ws/admin"| Relay["Relay Proxy :8001"]
  Relay <-->|"WebSocket /ws/agent"| Agent["Client Agent"]
  Admin -->|"HTTP/Jinja/REST"| API["API Server :8000"]
  API --> DB["SQLite/PostgreSQL"]
  API --> Artifacts["Artifact Storage"]
  Agent --> Sandbox["sandbox_root/machine_id/job_id"]
```

Responsibilities:

- API: authentication, admin pages, REST endpoints, DB, artifacts, audit.
- Relay: WebSocket auth, registry, controller lock, frame/command forwarding.
- Agent: consent banner, fake/real mode, sandbox, screen frames, commands.

