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

## Chapter 5: Implementation

The project uses Python 3.11, FastAPI, SQLAlchemy async, Jinja2, WebSocket relay endpoints, and a Python agent. Shared Pydantic envelopes keep relay protocol messages consistent.

The agent now uses provider abstractions for screen capture, process operations, application launch, webcam, input, and sandbox jobs. Each provider has fake and real implementations, and real providers return clear errors when optional Windows dependencies are missing. The UI includes machine audit filters and sandbox/job history views.

New UI implementation files include `apps/api/templates/base.html`, `dashboard.html`, `machines.html`, `machine_detail.html`, partials under `apps/api/templates/partials`, dashboard/shell CSS under `apps/api/static/css`, and page/relay JS under `apps/api/static/js`. New API support includes dashboard summary/recent-audit endpoints, per-machine sandbox aliases, and audited machine action endpoints for application, process, screen, webcam, and power requests.

## Chapter 6: Testing

The test suite contains 42 tests covering auth, ACL, protocol validation, sandbox defense, audit redaction, command policy, enrollment, machine listing, session lock, audit order, file/job flow, relay frame forwarding, WS ticket auth, observer/controller enforcement, relay audit bridge queueing, status transitions, optional dependency fallback, audit filters, job history, dashboard APIs, page rendering, per-machine audit filtering, protected process denial, power confirmation/reason checks, and sandbox alias routes.

## Chapter 7: Conclusion

TelePC is runnable as a local lab demo with API, relay, and fake agent. Remaining work is mainly production hardening: persisted heartbeat status, internal audit bridge persistence, stronger browser WS ticket flow, and broader real-agent validation.
