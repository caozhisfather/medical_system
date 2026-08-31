$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath 'D:\cc项目\ai+medicine'
conda activate ai-medicine-backend
python -m backend.app.main
