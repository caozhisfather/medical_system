$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

$condaRoot = Split-Path (Split-Path $env:CONDA_EXE -Parent) -Parent
$condaHook = Join-Path $condaRoot "shell\condabin\conda-hook.ps1"
if (Test-Path -LiteralPath $condaHook) {
    & $condaHook
}
conda activate pytorch_env

Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
python -m backend.app.main
