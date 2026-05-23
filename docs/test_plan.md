# Test Plan

Unit coverage:

- Password hashing and token encode/decode.
- Role permission matrix.
- WebSocket envelope validation.
- Sandbox path traversal and extension policy.
- Audit redaction.
- Process PID validation and job runner allowlist.

Integration coverage:

- Login returns token.
- Enrollment token creates machine and machine secret.
- Machine list endpoint.
- Control session lock denies second controller.
- Per-machine audit logs newest first.
- File upload, dispatch, and job record flow.
- Relay fake agent frame forwarding.

Commands:

```powershell
python -m compileall .
pytest -q
```

