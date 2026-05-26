# TelePC Technical Report

## Chapter 1: Introduction

TelePC demonstrates a browser-based remote desktop control model for authorized lab machines. The system separates browser administration, relay forwarding, and client-agent execution.

## Chapter 2: Theory

The design uses HTTP for authentication and administration, WebSocket for low-latency bidirectional messaging, role-based access control for admin permissions, and sandboxing to constrain file/job operations.

## Chapter 3: Requirements Analysis

Functional requirements include multi-machine listing, enrollment, control sessions, live screen frames, process/application commands, file sandbox, jobs, audit logs, and fake-agent demo mode. Non-functional requirements include visible consent, no credential collection, audit redaction, and local SQLite startup.

## Chapter 4: Design

The API server owns persistent state and HTML pages. The relay owns transient WebSocket connection state and controller locks. The agent owns machine-local actions and sandbox path enforcement.

The hardened design adds short-lived WebSocket tickets so the browser does not expose long-lived admin tokens to JavaScript. Relay-to-API calls use an internal shared secret. Relay audit writes are sent through a background queue so audit failures cannot break active WebSocket sessions. Machine status is persisted through explicit online, stale, and offline transitions.

The teacher UI prototypes were applied as real product surfaces. `Topic01_Prototype.html` drives the bright admin dashboard and machine list: left navigation groups, dashboard cards, workstation table, and recent audit activity. `remote_control_web_prototype.html` drives the dark single-machine shell: connected topbar, module sidebar, Applications, Processes, Screen, Keyboard Demo, Files, Webcam, Power, and per-machine Audit Logs. Static prototype data was replaced with API calls and relay WebSocket events.

UI description for submission screenshots:

- Dashboard: light administrative layout with a dark left sidebar, four metric cards, workstation table, search/refresh controls, and recent audit feed.
- Machines: searchable/filterable table with hostname, machine id, OS, status pill, last seen, active controller, and Manage action.
- Machine detail: dark remote shell with connected topbar, machine metadata header, module sidebar, screen frame viewer, sandbox panel, consent notices, confirmation modal, and per-machine audit panel.
- Safety UI: webcam consent checkbox, Keyboard Demo text area scoped to browser input only, controller-ack wait before input forwarding, Power reason modal, and sandbox-only file messaging.

## Chapter 5: Implementation

The project uses Python 3.11, FastAPI, SQLAlchemy async, Jinja2, WebSocket relay endpoints, and a Python agent. Shared Pydantic envelopes keep relay protocol messages consistent.

The agent now uses provider abstractions for screen capture, process operations, application launch, webcam, input, and sandbox jobs. Each provider has fake and real implementations, and real providers return clear errors when optional Windows dependencies are missing. The UI includes machine audit filters and sandbox/job history views.

New UI implementation files include `apps/api/templates/base.html`, `dashboard.html`, `machines.html`, `machine_detail.html`, partials under `apps/api/templates/partials`, dashboard/shell CSS under `apps/api/static/css`, and page/relay JS under `apps/api/static/js`. New API support includes dashboard summary/recent-audit endpoints, per-machine sandbox aliases, and audited machine action endpoints for application, process, screen, webcam, and power requests.

## Chapter 6: Testing

The test suite contains 42 tests covering auth, ACL, protocol validation, sandbox defense, audit redaction, command policy, enrollment, machine listing, session lock, audit order, file/job flow, relay frame forwarding, WS ticket auth, observer/controller enforcement, relay audit bridge queueing, status transitions, optional dependency fallback, audit filters, job history, dashboard APIs, page rendering, per-machine audit filtering, protected process denial, power confirmation/reason checks, and sandbox alias routes.

## Chapter 7: Conclusion

TelePC is runnable as a local lab demo with API, relay, and fake agent. Remaining work is mainly production hardening: persisted heartbeat status, internal audit bridge persistence, stronger browser WS ticket flow, and broader real-agent validation.
## Chapter 4: Relay Proxy Architecture

The relay accepts authenticated agent and admin WebSockets. Admin WebSockets use a short-lived single-use ticket issued by the API from the session cookie. Agents authenticate with their machine secret. The relay broadcasts agent frames/results to observers, but protected command forwarding is gated by the API-owned active control session.

## Chapter 5: Frontend, Backend, and Agent Breakdown

The frontend uses Jinja pages plus static JavaScript. Dashboard and machine views fetch live API data, then use the relay WebSocket for frames and command results. The backend owns users, roles, machines, sessions, artifacts, sandbox records, jobs, and audit logs. The agent owns machine-local providers for screen, input, applications, processes, files, jobs, webcam, and power, with fake mode available for CI and demos.

## Chapter 6: Real Machine Test Results

Automated verification on 2026-05-26:

- `py -3.12 -m compileall .`: passed
- `py -3.12 -m pytest -q`: passed, 72 tests

Physical Windows lab validation is tracked in `docs/REAL_MACHINE_TEST_CHECKLIST.md`.

## Chapter 7: Limitations and Future Work

- Real input and real power remain environment-gated by design.
- Large file dispatch prepares a download URL payload; full signed URL serving can be expanded if large real-machine transfers are required.
- Physical validation is still needed for camera availability, screen FPS stability, and Windows power command behavior.
