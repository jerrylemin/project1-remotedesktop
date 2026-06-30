# TelePC Real Machine Test Checklist

This checklist is the only remaining gate for a literal 100/100 score. Do not fake these artifacts. Run it on an authorized Windows lab machine with the TelePC client visible to the local user.

## Evidence Files Required

Save proof under `artifacts/physical_validation/`:

- `01_connected_machine.png`
- `02_consent_popup.png`
- `03_app_whitelist.png`
- `04_file_whitelist.png`
- `05_webcam_devices.png`
- `06_keylogger_lab_module.png`
- `07_audit_logs.png`
- `validation_notes.md`

## Manual Validation Steps

1. Run the API server.
2. Run the relay.
3. Run `TelePCClient.exe` on the controlled Windows machine with a registered machine token.
4. Log in as admin.
5. Confirm only real connected machines appear in production mode.
6. Confirm the application whitelist shows Zalo, Discord, VSCode, Chrome, and Notepad.
7. Start an allowlisted app and confirm the local consent popup appears on the client.
8. Deny the app action and verify no execution.
9. Approve the same exact app action and verify execution.
10. Confirm the process list shows background processes, PID, memory, and CPU.
11. For process kill, use only a harmless test process such as a manually opened Notepad instance.
12. Create `C:\Remote` on the controlled machine and add a harmless test file.
13. Confirm the file browser shows only discovered `X:\Remote` roots that exist.
14. Confirm `..\secret.txt`, absolute relative-path override, UNC paths, and system paths are rejected.
15. Confirm webcam enumeration renders built-in and/or USB device names when present.
16. Confirm webcam frames do not start before approved local consent.
17. Confirm the Keylogger Lab Module requires local popup consent, has TTL, can stop, and redacts sensitive-window events.
18. Confirm audit logs include request, approval, denial, timeout, execution, and failure events with consent id and command id where applicable.
19. Save screenshots and notes to the required evidence paths above.

## Safe Operator Rules

- Do not run real restart or shutdown unless the lab explicitly authorizes it.
- Do not kill system processes.
- Do not capture real credentials or payment details.
- Do not leave key capture running after the test; stop it and wait for TTL expiry.
- Keep the controlled-machine console visible.

## Helper

Run this guide script if you want prompts and path checks:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_physical_lab_validation.ps1
```
