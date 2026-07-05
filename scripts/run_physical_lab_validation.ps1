param(
    [string]$EvidenceDir = "artifacts\physical_validation"
)

$ErrorActionPreference = "Stop"

function Step([string]$Title, [string]$Body) {
    Write-Host ""
    Write-Host "== $Title ==" -ForegroundColor Cyan
    Write-Host $Body
    Read-Host "Press Enter after completing this step, or Ctrl+C to stop"
}

New-Item -ItemType Directory -Force $EvidenceDir | Out-Null

Write-Host "TelePC physical lab validation guide" -ForegroundColor Green
Write-Host "This script does not execute destructive actions. It only guides manual proof collection."
Write-Host "Evidence directory: $EvidenceDir"

Step "1. Run API" "Start the API on the controller machine and confirm /health returns 200."
Step "2. Run relay" "Start the relay and confirm agent/admin WebSocket endpoints are listening."
Step "3. Run client" "Run TelePCClient.exe on the controlled Windows machine with a registered token in a visible console."
Step "4. Login" "Log in as admin from the controller browser."
Step "5. Real machine list" "Confirm only the real connected machine appears. Save $EvidenceDir\01_connected_machine.png."
Step "6. Application whitelist" "Confirm Zalo, Discord, VSCode, Chrome, and Notepad appear. Save $EvidenceDir\03_app_whitelist.png."
Step "7. Consent popup deny" "Start a harmless app, capture the local popup, click No, and confirm no execution. Save $EvidenceDir\02_consent_popup.png."
Step "8. Consent popup approve" "Repeat the exact app command, click Yes within 15 seconds, and confirm execution."
Step "9. Process module" "Confirm background processes, PID, CPU, and memory appear. Kill only a harmless manually opened Notepad test process."
Step "10. File whitelist" "Create C:\Remote with a harmless test file. Confirm only existing X:\Remote roots appear and path traversal/system paths are rejected. Save $EvidenceDir\04_file_whitelist.png."
Step "11. Webcam devices" "Enumerate webcams. Confirm built-in/USB devices render when present and start is disabled until a real device is selected. Save $EvidenceDir\05_webcam_devices.png."
Step "12. Webcam consent" "Start webcam only after local approval. Confirm no frame is sent before approval, then stop it."
Step "13. Keylogger Lab Module" "Start key capture only after local approval, verify TTL/stop, and avoid credentials. Save $EvidenceDir\06_keylogger_lab_module.png."
Step "14. Audit logs" "Confirm request, approval, denial, timeout, execution, and failure events are visible. Save $EvidenceDir\07_audit_logs.png."

$notes = Join-Path $EvidenceDir "validation_notes.md"
if (-not (Test-Path $notes)) {
    @"
# TelePC Physical Validation Notes

Date/time:
Operator:
Admin machine:
Client machine:
Client EXE path:
API command:
Relay command:
Login user:

Results:

- Machine connected proof:
- App whitelist:
- Consent deny:
- Consent timeout:
- Consent approve:
- Process module:
- File whitelist:
- Webcam test:
- Keylogger TTL/stop test:
- Audit log test:

Known limitations:

"@ | Set-Content -Encoding UTF8 $notes
}

Write-Host ""
Write-Host "Manual guide complete. Fill in $notes and attach the required screenshots." -ForegroundColor Green
