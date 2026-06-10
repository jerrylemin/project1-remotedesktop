$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$SubmissionDir = Join-Path $Root "artifacts\submission"
$ZipPath = Join-Path $SubmissionDir "telepc_submission.zip"

New-Item -ItemType Directory -Force -Path $SubmissionDir | Out-Null

Get-ChildItem -Path $Root -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
foreach ($cache in @(".pytest_cache", ".ruff_cache")) {
    $path = Join-Path $Root $cache
    if (Test-Path $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}
foreach ($db in @("telepc.db", "telepc.sqlite", ".env")) {
    $path = Join-Path $Root $db
    if (Test-Path $path) {
        Remove-Item -LiteralPath $path -Force
    }
}
if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

$exclude = @(
    ".git",
    "artifacts\submission",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    "graphify-out",
    ".env",
    "telepc.db",
    "telepc.sqlite"
)

$items = Get-ChildItem -Path $Root -Force | Where-Object {
    $name = $_.Name
    -not ($exclude | Where-Object { $_ -eq $name })
}

Compress-Archive -Path $items.FullName -DestinationPath $ZipPath -Force
Write-Host "Submission zip created: $ZipPath"
