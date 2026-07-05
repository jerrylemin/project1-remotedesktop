# TelePC threat model

## Scope and assets

Authorized lab control only. Protected assets are user/admin sessions, machine secrets, consent decisions, command routing, controlled-machine files/processes/cameras/key events, and audit integrity.

## Trust boundaries

| Boundary | Untrusted input | Enforcement |
|---|---|---|
| Browser → API | credentials, role-shaped fields, machine IDs, action payloads | JWT/cookie auth, permissions, grants, Pydantic bounds, exact consent |
| Browser → relay | ticket, origin, machine ID, command envelope | single-use ticket, origin allowlist, controller lock, exact consent consumption |
| Relay → API | machine status, consent decision, command authorization | internal secret and server-derived actor/machine identity |
| Agent → relay | machine secret, envelope machine ID, frames/results | secret verification, current-socket and authenticated-machine pinning |
| Agent → Windows | PID, app key, path, webcam ID, key capture | protected process/app allowlists, discovered roots, selected devices, local consent |
| Audit/artifacts | metadata, filenames, captured values | redaction, bounds, sandbox containment, no persistent key storage |

## Threat actors

Anonymous network client, authenticated read-only/auditor, teacher without a grant, compromised browser session, stale/reconnected agent, malicious or malformed controlled-machine response, and accidental operator misuse.

## Denied capabilities

Stealth/persistence, antivirus bypass, raw administrator-supplied shell commands, arbitrary file browsing, silent webcam/key capture, critical process termination, production fake agents, secret logging, and forged physical evidence.

## Residual boundary

Automated tests cannot prove Windows popup focus, real junction semantics on the lab volume, USB camera behavior, antivirus/firewall interaction, or the packaged EXE on a second physical machine. Those remain the explicit physical gate.
