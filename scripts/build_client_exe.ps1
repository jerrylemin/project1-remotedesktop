param(
    [switch]$InstallPyInstaller
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")

Set-Location $RepoRoot

if ($InstallPyInstaller) {
    python -m pip install pyinstaller
}

python -m scripts.package_client_exe

$Artifact = Join-Path $RepoRoot "dist\TelePCClient.exe"
if (-not (Test-Path $Artifact)) {
    throw "Expected artifact was not created: $Artifact"
}

Write-Host "Built $Artifact"
