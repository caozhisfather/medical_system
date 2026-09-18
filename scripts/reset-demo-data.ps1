[CmdletBinding()]
param(
    [switch]$KeepAuth
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Runtime = Join-Path $Root "runtime"
$Backup = Join-Path $Runtime ("backups\" + (Get-Date -Format "yyyyMMdd-HHmmss"))
New-Item -ItemType Directory -Force -Path $Backup | Out-Null

foreach ($port in @(8000, 5173)) {
    $owner = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue)
    if ($owner.Count -gt 0) {
        throw "Port $port is still in use. Run scripts\stop-project.ps1 before resetting demo data."
    }
}

$files = @(
    "data\exam_questions.json",
    "data\training_sessions.json",
    "data\teacher_case_workbench.json",
    "data\audit_logs.jsonl",
    "data\skills.sqlite3",
    "data\skills.sqlite3-journal",
    "data\skills.sqlite3-wal",
    "data\skills.sqlite3-shm"
)
if (-not $KeepAuth) {
    $files += @(
        "data\auth.sqlite3",
        "data\auth.sqlite3-journal",
        "data\auth.sqlite3-wal",
        "data\auth.sqlite3-shm"
    )
}

$moved = 0
foreach ($relative in $files) {
    $source = Join-Path $Root $relative
    if (Test-Path -LiteralPath $source) {
        $destination = Join-Path $Backup ([IO.Path]::GetFileName($source))
        Move-Item -LiteralPath $source -Destination $destination -Force
        $moved++
    }
}

Write-Output "Demo runtime data reset complete."
Write-Output "Backed up $moved file(s) to: $Backup"
if ($KeepAuth) {
    Write-Output "Authentication database was preserved."
} else {
    Write-Output "Authentication database was reset; demo accounts will be seeded on next backend start."
}
