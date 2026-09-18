[CmdletBinding()]
param(
    [int[]]$Ports = @(8000, 5173)
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateFile = Join-Path $Root "runtime\processes.json"

function Get-Children([int]$ParentId, [object[]]$AllProcesses) {
    $children = @($AllProcesses | Where-Object { $_.ParentProcessId -eq $ParentId })
    foreach ($child in $children) {
        @($child.ProcessId) + @(Get-Children $child.ProcessId $AllProcesses)
    }
}

$targets = @()
if (Test-Path -LiteralPath $StateFile) {
    try {
        $state = Get-Content -LiteralPath $StateFile -Raw | ConvertFrom-Json
        $targets += @($state.backend.wrapper_pid, $state.frontend.wrapper_pid)
    } catch {
        Write-Warning "Could not read runtime process state; checking known project processes."
    }
}

$allProcesses = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue)
foreach ($port in $Ports) {
    $owners = @(Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique)
    foreach ($owner in $owners) {
        $process = $allProcesses | Where-Object { $_.ProcessId -eq $owner } | Select-Object -First 1
        if ($process -and $process.CommandLine -match "backend\.app\.main|vite|pnpm") {
            $targets += $owner
        } else {
            Write-Warning "Port $port is owned by PID $owner and was not recognized as a project process."
        }
    }
}

$targets = @($targets | Where-Object { $_ } | ForEach-Object { [int]$_ } | Select-Object -Unique)
$descendants = foreach ($target in $targets) { Get-Children $target $allProcesses }
$killIds = @($targets + $descendants | Select-Object -Unique | Sort-Object -Descending)
foreach ($id in $killIds) {
    Stop-Process -Id $id -Force -ErrorAction SilentlyContinue
}

if (Test-Path -LiteralPath $StateFile) {
    Remove-Item -LiteralPath $StateFile -Force
}
Write-Output "Project stop requested. Any unrelated process on a required port was left untouched."
