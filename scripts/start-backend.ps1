param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (-not (Test-Path -LiteralPath "env\.env")) {
    New-Item -ItemType Directory -Force -Path "env" | Out-Null
    Copy-Item -LiteralPath ".env.example" -Destination "env\.env" -Force
}

& $Python -m pip install -r requirements.txt
& $Python -m backend.app.main
