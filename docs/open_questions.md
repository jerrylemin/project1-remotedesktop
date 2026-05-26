# Open Questions

- Should relay audit writes be persisted through a private internal API endpoint or direct DB access? Default chosen: private API stub, non-blocking.
- Resolved: browser WS auth uses a short-lived single-use ticket issued from the HttpOnly session cookie. No long-lived token is stored in localStorage.
- What exact real-agent commands are allowed in the lab? Default chosen: conservative allowlist from `.env.example`.
- Should heartbeat stale/offline updates be relay-only or persisted to API DB? Default chosen: relay registry now, DB persistence later.
