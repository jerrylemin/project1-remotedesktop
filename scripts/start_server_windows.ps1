param(
    [switch]$FakeAgents
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
Set-Location -LiteralPath $Root

function Ensure-FirewallRule {
    param(
        [string]$Name,
        [int]$Port
    )
    $existing = Get-NetFirewallRule -DisplayName $Name -ErrorAction SilentlyContinue
    if (-not $existing) {
        New-NetFirewallRule -DisplayName $Name -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port | Out-Null
    }
}

try {
    Ensure-FirewallRule -Name "TelePC API 8000" -Port 8000
    Ensure-FirewallRule -Name "TelePC Relay 8001" -Port 8001
} catch {
    Write-Warning "Firewall rule update skipped: $($_.Exception.Message)"
}

Write-Host "Starting TelePC API and Relay on 0.0.0.0:8000 and 0.0.0.0:8001"
$api = Start-Process -FilePath "py" -ArgumentList "-3.12", "scripts/run_api.py", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $Root -PassThru
$relay = Start-Process -FilePath "py" -ArgumentList "-3.12", "scripts/run_relay.py", "--host", "0.0.0.0", "--port", "8001" -WorkingDirectory $Root -PassThru
$agents = $null
if ($FakeAgents) {
    $agents = Start-Process -FilePath "py" -ArgumentList "-3.12", "scripts/run_3_fake_agents.py" -WorkingDirectory $Root -PassThru
}

try {
    Wait-Process -Id $api.Id, $relay.Id
} finally {
    foreach ($proc in @($api, $relay, $agents)) {
        if ($proc -and -not $proc.HasExited) {
            Stop-Process -Id $proc.Id -Force
        }
    }
}
