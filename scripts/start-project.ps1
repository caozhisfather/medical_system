[CmdletBinding()]
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173,
    [switch]$Restart
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Runtime = Join-Path $Root "runtime"
$LogDir = Join-Path $Runtime "logs"
$StateFile = Join-Path $Runtime "processes.json"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Get-PortOwners([int]$Port) {
    @(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique)
}

function Quote-PowerShell([string]$Value) {
    "'" + $Value.Replace("'", "''") + "'"
}

function Encode-PowerShell([string]$Script) {
    [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Script))
}

function Wait-Port([int]$Port, [int]$TimeoutSeconds = 30) {
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if ((Get-PortOwners $Port).Count -gt 0) { return $true }
        Start-Sleep -Milliseconds 500
    } while ((Get-Date) -lt $deadline)
    return $false
}

if ($Restart) {
    & (Join-Path $PSScriptRoot "stop-project.ps1") -ErrorAction SilentlyContinue
}

$occupied = @(
    [PSCustomObject]@{ Name = "backend"; Port = $BackendPort; Owners = @(Get-PortOwners $BackendPort) }
    [PSCustomObject]@{ Name = "frontend"; Port = $FrontendPort; Owners = @(Get-PortOwners $FrontendPort) }
) | Where-Object { $_.Owners.Count -gt 0 }
if ($occupied.Count -gt 0) {
    $details = ($occupied | ForEach-Object { "$($_.Name) port $($_.Port), PID $($_.Owners -join ',')" }) -join "; "
    throw "Required port is already in use: $details. Stop the existing service or rerun with -Restart."
}

$condaCommand = Get-Command conda.exe -ErrorAction SilentlyContinue
if (-not $condaCommand) {
    throw "conda.exe was not found. Install Conda and make sure pytorch_env is available."
}
$pnpmCommand = Get-Command pnpm.cmd -ErrorAction SilentlyContinue
if (-not $pnpmCommand) {
    $pnpmCommand = Get-Command pnpm -ErrorAction SilentlyContinue
}
if (-not $pnpmCommand) {
    throw "pnpm was not found. Enable Corepack or install pnpm before starting the project."
}

$rootArg = Quote-PowerShell $Root
$condaArg = Quote-PowerShell $condaCommand.Source
$backendLogArg = Quote-PowerShell (Join-Path $LogDir "backend.log")
$frontendLogArg = Quote-PowerShell (Join-Path $LogDir "frontend.log")
$frontendErrArg = Quote-PowerShell (Join-Path $LogDir "frontend-error.log")
$backendErrArg = Quote-PowerShell (Join-Path $LogDir "backend-error.log")

$backendScript = @"
`$ErrorActionPreference = 'Stop'
`$env:PYTHONUTF8 = '1'
`$env:DEMO_MODE = 'true'
`$env:BACKEND_RELOAD = 'false'
`$env:BACKEND_PORT = '$BackendPort'
`$env:RAG_PROVIDER = 'local'
`$env:TTS_PROVIDER = 'placeholder'
`$env:DIGITAL_HUMAN_MODE = 'mock'
Set-Location -LiteralPath $rootArg
`$conda = $condaArg
(& `$conda 'shell.powershell' 'hook') | Out-String | Invoke-Expression
conda activate pytorch_env
python -m backend.app.main
"@

$frontendScript = @"
`$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $rootArg
`$env:VITE_API_TARGET = 'http://127.0.0.1:$BackendPort'
& '$($pnpmCommand.Source)' --dir frontend exec vite --host 127.0.0.1 --port $FrontendPort
"@

$backendProcess = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $Root `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", (Encode-PowerShell $backendScript)) `
    -RedirectStandardOutput (Join-Path $LogDir "backend.log") `
    -RedirectStandardError (Join-Path $LogDir "backend-error.log") -PassThru
$frontendProcess = Start-Process -FilePath "powershell.exe" -WindowStyle Hidden -WorkingDirectory $Root `
    -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-EncodedCommand", (Encode-PowerShell $frontendScript)) `
    -RedirectStandardOutput (Join-Path $LogDir "frontend.log") `
    -RedirectStandardError (Join-Path $LogDir "frontend-error.log") -PassThru

@{
    started_at = (Get-Date).ToUniversalTime().ToString("o")
    root = $Root
    backend = @{ wrapper_pid = $backendProcess.Id; port = $BackendPort }
    frontend = @{ wrapper_pid = $frontendProcess.Id; port = $FrontendPort }
} | ConvertTo-Json | Set-Content -LiteralPath $StateFile -Encoding UTF8

$backendReady = Wait-Port $BackendPort
$frontendReady = Wait-Port $FrontendPort
if (-not $backendReady -or -not $frontendReady) {
    Write-Warning "One or more services did not open their port. Check runtime/logs."
    if (Test-Path -LiteralPath $StateFile) {
        Get-Content -LiteralPath $StateFile
    }
    exit 1
}

Write-Output "Project started in competition demo mode."
Write-Output "Frontend: http://127.0.0.1:$FrontendPort/"
Write-Output "Backend:  http://127.0.0.1:$BackendPort/"
Write-Output "Health:   http://127.0.0.1:$BackendPort/api/health"
Write-Output "Logs:     $LogDir"
