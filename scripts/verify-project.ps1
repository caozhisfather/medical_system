[CmdletBinding()]
param(
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$FrontendUrl = "http://127.0.0.1:5173",
    [switch]$AllowDevelopmentMode
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$passed = 0
$failed = 0

function Check([string]$Name, [scriptblock]$Action) {
    try {
        & $Action
        Write-Output "[PASS] $Name"
        $script:passed++
    } catch {
        Write-Output "[FAIL] $Name :: $($_.Exception.Message)"
        $script:failed++
    }
}

Check "pytorch_env is active" {
    if ($env:CONDA_DEFAULT_ENV -ne "pytorch_env") {
        throw "Current environment is '$env:CONDA_DEFAULT_ENV'. Run this script after conda activate pytorch_env."
    }
}

$health = $null
Check "backend health endpoint" {
    $script:health = Invoke-RestMethod -Uri "$BackendUrl/api/health" -TimeoutSec 15
    if ($health.status -ne "ok") { throw "status is not ok" }
    if ($health.readiness -ne "ready") { throw "readiness is $($health.readiness)" }
}

Check "competition demo mode" {
    if (-not $AllowDevelopmentMode -and $health.demo_mode -ne $true) {
        throw "DEMO_MODE is not enabled. Start with scripts/start-project.ps1 or pass -AllowDevelopmentMode."
    }
}

Check "frontend entry page" {
    $page = Invoke-WebRequest -Uri "$FrontendUrl/" -UseBasicParsing -TimeoutSec 15
    if ($page.StatusCode -ne 200 -or $page.Content -notmatch '<div id="app"></div>') {
        throw "frontend entry page is not usable"
    }
}

$requiredFiles = @(
    "data\anatomy.json",
    "data\anatomy_term_glossary.json",
    "data\anatomy_textbook.json",
    "data\anatomy_asset_graph.json",
    "data\exam_settings.json",
    "frontend\public\anatomy\atlas.json",
    "frontend\public\anatomy\organs.json"
)
foreach ($relative in $requiredFiles) {
    Check "required asset $relative" {
        $path = Join-Path $Root $relative
        if (-not (Test-Path -LiteralPath $path)) { throw "missing file" }
        if ((Get-Item -LiteralPath $path).Length -le 0) { throw "empty file" }
    }
}

$studentToken = $null
Check "student demo login" {
    $body = @{ account = "student"; password = "student123"; role = "student" } | ConvertTo-Json
    $login = Invoke-RestMethod -Method Post -Uri "$BackendUrl/api/auth/login" -ContentType "application/json" -Body $body -TimeoutSec 15
    $script:studentToken = $login.token
    if (-not $studentToken) { throw "no session token returned" }
}

$headers = @{}
if ($studentToken) { $headers = @{ Authorization = "Bearer $studentToken" } }
Check "authenticated anatomy endpoint" {
    $items = Invoke-RestMethod -Uri "$BackendUrl/api/anatomy" -Headers $headers -TimeoutSec 15
    if (@($items).Count -lt 1) { throw "anatomy exercise list is empty" }
}

Check "anatomy graph endpoint" {
    $graph = Invoke-RestMethod -Uri "$BackendUrl/api/graph?scope=anatomy" -Headers $headers -TimeoutSec 15
    if (@($graph.nodes).Count -lt 100 -or @($graph.edges).Count -lt 100) {
        throw "anatomy graph is unexpectedly small"
    }
}

Check "local textbook retrieval" {
    $textbook = Invoke-RestMethod -Uri "$BackendUrl/api/anatomy/textbook?q=心脏" -TimeoutSec 15
    if ($textbook.found -ne $true) { throw "no textbook result for 心脏" }
}

Check "anatomy graph consistency" {
    $output = @(python -X utf8 (Join-Path $Root "scripts\validate_anatomy_graph.py"))
    if ($LASTEXITCODE -ne 0) { throw ($output -join " ") }
    if (($output -join " ") -notmatch '"result":\s*"PASS"') { throw "validator did not report PASS" }
}

Check "no tracked secret pattern" {
    $matches = @(git -C $Root grep -n -I -E "OPENAI_API_KEY=.+|MAIL_PASSWORD=.+|sk-[A-Za-z0-9]{16,}" -- . 2>$null |
        Where-Object { $_ -notmatch "your-|example|placeholder|<.*>|CHANGE_ME" })
    if ($matches.Count -gt 0) { throw ($matches -join "; ") }
}

Write-Output ""
Write-Output "Verification summary: $passed passed, $failed failed."
if ($failed -gt 0) { exit 1 }
Write-Output "Competition stability gate: PASS"
