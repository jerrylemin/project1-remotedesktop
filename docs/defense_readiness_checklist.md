# Defense readiness checklist

Date: 2026-05-30

## Strict prompt re-audit, 2026-06-01

- [x] Compile, tests, and lint pass locally.
- [x] Relay machine secret is verified.
- [x] Machine grants are enforced.
- [x] Sensitive API commands require durable consent records.
- [x] One-file client packaging script exists.
- [x] `dist\TelePCClient.exe` was built and smoke-tested with `--help`.
- [x] Fake/demo agents are isolated from production startup and production UI by default.
- [x] Application whitelist exactly matches Zalo, Discord, VSCode, Chrome, and Notepad.
- [x] File access module uses only existing `X:\Remote` folders on the controlled machine.
- [x] Webcam module enumerates available devices before start.
- [x] Native local popup has Yes, No, and 15-second timeout behavior.
- [ ] Physical Windows lab validation has confirmed real webcam/device/file/popup behavior end to end.

- [x] All tests pass.
- [x] Lint passes.
- [x] Health endpoint works.
- [x] Relay machine secret is verified.
- [x] Machine grants are enforced.
- [x] Sensitive commands require consent.
- [x] Screenshot does not stream before consent.
- [x] Webcam does not start before consent.
- [x] File download is sandboxed.
- [x] Power commands are demo-safe by default.
- [x] Lab-real mode requires explicit opt-in.
- [x] Audit logs record all sensitive commands.
- [x] README has runnable demo instructions.
- [x] Submission cleanup script exists.
