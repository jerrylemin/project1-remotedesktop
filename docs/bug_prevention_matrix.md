# TelePC bug-prevention matrix

| Bug ID | Category | Scenario | Prevention | Test/evidence | Status |
|---|---|---|---|---|---|
| AUTH-001 | Authentication | Repeated password guessing | Per-IP+username failure window | `test_auth_security.py` | PREVENTED |
| AUTH-002 | Authentication | Unknown-user timing shortcut | Dummy PBKDF2 verification | login tests | PREVENTED |
| AUTH-003 | Authentication | Default password seeded/printed | Explicit bootstrap only; secure prompt | auth security test | PREVENTED |
| AUTHZ-001 | Authorization | Teacher/auditor/agent crosses machine boundary | Permission plus grant checks | grant/WS tests | PREVENTED |
| CONS-001 | Consent | Same type, different payload/user/machine | Canonical exact hash | consent fuzz tests | PREVENTED |
| CONS-002 | Consent | Identical payload borrows another command approval | Command ID propagated and consumed | command-ID test | PREVENTED |
| CONS-003 | Consent | Approval replay/double click | Single-use `consumed` status | consent/race tests | PREVENTED |
| CONS-004 | Consent | Browser forges local approval | Agent-authenticated relay records decision | relay integration test | PREVENTED |
| RELAY-001 | Relay | FIFO/out-of-order result misrouting | Session-ID waiter map | routing contract test | PREVENTED |
| RELAY-002 | Relay | Old socket emits after reconnect | Close/replace and current-socket guard | race test | PREVENTED |
| RELAY-003 | Relay | Agent spoofs another machine ID | Pin envelope to authenticated machine | routing test | PREVENTED |
| RELAY-004 | Relay | Cross-origin browser WebSocket | Existing origin allowlist enforced | routing test | PREVENTED |
| APP-001 | Application | Raw/space/confusable app key | Exact normalized allowlist key | app fuzz test | PREVENTED |
| APP-002 | Application | Windows path splits at spaces | Native subprocess argv arrays | app launch test | PREVENTED |
| PROC-001 | Process | PID reused after consent | Compare live process name before terminate | process module test | PREVENTED |
| PROC-002 | Process | AccessDenied/disappearing process or NaN breaks list | Skip bad row; finite non-negative metrics | process module test | PREVENTED |
| FILE-001 | File | Traversal/UNC/absolute/symlink/junction escape | Resolve and contain under discovered root | file fuzz tests | PREVENTED |
| FILE-002 | File | Windows device/trailing/overlong name | Component validation | Windows path tests | PREVENTED |
| FILE-003 | File | Large download exhausts memory | Bounded read (`limit + 1`) | Windows path test | PREVENTED |
| CAM-001 | Webcam | Snapshot silently uses camera 0 | Open exact consented ID, finally release | webcam provider test | PREVENTED |
| CAM-002 | Webcam | Repeated start/unplug/disconnect leaks handle | Release-before-start and disconnect cleanup | provider/unit tests | PREVENTED |
| KEY-001 | Keylogger | Empty consent defaults to approval | Default deny | race test | PREVENTED |
| KEY-002 | Keylogger | TTL needs later key/event to stop | Independent daemon timer | race test | PREVENTED |
| KEY-003 | Keylogger | Multiple listeners or disconnect persistence | Single active session plus disconnect reset | race/keylogger tests | PREVENTED |
| AUD-001 | Audit | Secret variants or oversized metadata leak/bloat | Expanded redaction and 16 KiB bound | audit security test | PREVENTED |
| UI-001 | UI | Keylogger shows active before result/after TTL | Await result and expiry timer | UI contract test | PREVENTED |
| ENV-001 | Environment | Invalid FPS/quality dimensions crash agent | Safe integer fallbacks/clamps | environment test | PREVENTED |
| PHY-001 | Physical | OS/hardware behavior differs from mocks | Required lab checklist/screenshots | physical evidence | MISSING |

Known TOCTOU limits (file content changing after consent, webcam unplug after enumeration) fail safely through containment/size/provider errors and require physical confirmation for complete evidence.
