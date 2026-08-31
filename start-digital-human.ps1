$ErrorActionPreference = "Stop"

$projectPath = "/mnt/d/cc项目/ai+medicine"
wsl.exe -d Ubuntu -- bash "$projectPath/scripts/start-digital-human-wsl.sh" "$projectPath"
