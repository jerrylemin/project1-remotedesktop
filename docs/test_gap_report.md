# TelePC test-gap report

| Area | Coverage added/verified | Remaining gap | Status |
|---|---|---|---|
| Authentication | rate limit, bounded input, no default/printed password | distributed multi-process limiter | SAFE LIMITATION |
| Authorization | roles, grants, controller lock, agent/web separation | real multi-admin lab session | MANUAL |
| Consent | payload fuzz, command ID, single use, deny/timeout/expiry | real popup timing/focus | MANUAL |
| Relay | auth, origin, current socket, machine pinning, result correlation | real network loss/reconnect | MANUAL |
| Application | exact five apps, raw/confusable keys, Windows argv | installed/missing status on lab PC | MANUAL |
| Process | invalid/critical/PID reuse, disappearing process, NaN | harmless real Notepad termination | MANUAL |
| File | traversal/UNC/symlink/reserved/size fuzz | real NTFS junction and 8.3 behavior | MANUAL |
| Webcam | no device/multiple IDs/selected snapshot/release | USB unplug and real frame start | MANUAL |
| Keylogger | deny/default, timer, one session, redaction, disconnect | real visible listener/TTL indicator | MANUAL |
| Audit | redaction, bounds, machine filter | screenshot of full lifecycle | MANUAL |
| UI | escaped HTML contracts, correlated results, TTL state | interactive browser race observation | MANUAL |
| Packaging | build, default real, help | run on second Windows machine without Python | MANUAL |

All automatable gaps identified in this pass now have tests. Manual rows map to `docs/REAL_MACHINE_TEST_CHECKLIST.md` and the eight missing evidence files.
