$ErrorActionPreference = "Stop"

$env:TELEPC_ENABLE_REAL_INPUT = "true"
$env:TELEPC_ENABLE_REAL_POWER = "true"
$env:TELEPC_REAL_MODE_CONFIRMED = "TELEPC_LAB_AUTHORIZED"

Write-Host "LAB REAL MODE ENABLED"
Write-Host "Real input: enabled"
Write-Host "Real power: enabled"
Write-Host "Mode: real"
Write-Host "Consent, RBAC, and audit logging are still required."

python client.py --mode real --confirm-real-mode TELEPC_LAB_AUTHORIZED @args
