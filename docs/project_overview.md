# Project Overview

TelePC is a web remote desktop control system for lab, demo, and authorized administration. Browser admins connect to a relay over WebSocket; client agents connect outbound to the same relay. The relay forwards frames, commands, and command results while enforcing a single controller lock per machine.

Scope:

- Multi-machine dashboard.
- Machine enrollment with one-time token and machine secret.
- Screen frame forwarding.
- Process/application list commands.
- File upload and sandbox dispatch.
- Sandbox jobs.
- Per-machine audit logs.
- Fake agent demo path.

Ethical limits:

- No stealth malware behavior.
- No credential, cookie, token, private key, or sensitive keystroke collection.
- Dangerous actions require explicit confirmation and audit.

