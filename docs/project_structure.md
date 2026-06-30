# Project Structure

```text
apps/api/          FastAPI API server, Jinja admin pages, DB models, routers, services
apps/relay/        WebSocket relay with machine registry, subscribers, controller lock
apps/agent/        Consent-visible real client agent, explicit demo/fake providers, sandbox, commands, screen frames
shared/            Protocol envelope, enums, redaction, time and crypto helpers
tests/unit/        Unit tests for security-sensitive primitives
tests/integration/ API and relay integration tests
scripts/           Local run scripts and admin seed script
docs/              Architecture, API, security, test, demo, report, and handoff docs
alembic/           Initial schema migration
```

Entry points:

- API: `apps.api.main:app` or `python scripts/run_api.py`
- Relay: `apps.relay.main:app` or `python scripts/run_relay.py`
- Demo agent: `python scripts/run_fake_agent.py` only for explicit development/test scenarios
- Real agent: `python scripts/run_agent.py` with `AGENT_MODE=real`

