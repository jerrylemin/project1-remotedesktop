# Open Questions

- Should relay audit writes be persisted through a private internal API endpoint or direct DB access? Default chosen: private API stub, non-blocking.
- Should browser WS token come from cookie-auth session, localStorage, or short-lived WS ticket? Default chosen: bearer token path for tests; UI flow needs refinement.
- What exact real-agent commands are allowed in the lab? Default chosen: conservative allowlist from `.env.example`.
- Should heartbeat stale/offline updates be relay-only or persisted to API DB? Default chosen: relay registry now, DB persistence later.

