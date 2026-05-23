# TelePC Technical Report

## Chapter 1: Introduction

TelePC demonstrates a browser-based remote desktop control model for authorized lab machines. The system separates browser administration, relay forwarding, and client-agent execution.

## Chapter 2: Theory

The design uses HTTP for authentication and administration, WebSocket for low-latency bidirectional messaging, role-based access control for admin permissions, and sandboxing to constrain file/job operations.

## Chapter 3: Requirements Analysis

Functional requirements include multi-machine listing, enrollment, control sessions, live screen frames, process/application commands, file sandbox, jobs, audit logs, and fake-agent demo mode. Non-functional requirements include visible consent, no credential collection, audit redaction, and local SQLite startup.

## Chapter 4: Design

The API server owns persistent state and HTML pages. The relay owns transient WebSocket connection state and controller locks. The agent owns machine-local actions and sandbox path enforcement.

## Chapter 5: Implementation

The project uses Python 3.11, FastAPI, SQLAlchemy async, Jinja2, WebSocket relay endpoints, and a Python agent. Shared Pydantic envelopes keep relay protocol messages consistent.

## Chapter 6: Testing

The test suite contains 21 tests covering auth, ACL, protocol validation, sandbox defense, audit redaction, command policy, enrollment, machine listing, session lock, audit order, file/job flow, and relay frame forwarding.

## Chapter 7: Conclusion

TelePC is runnable as a local lab demo with API, relay, and fake agent. Remaining work is mainly production hardening: persisted heartbeat status, internal audit bridge persistence, stronger browser WS ticket flow, and broader real-agent validation.

