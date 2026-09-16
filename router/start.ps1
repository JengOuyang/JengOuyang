# start.ps1 — 手動啟動 Router（第一次測試用）
$root = "C:\trade-desk"
Set-Location "$root\router"
& "$root\.venv\Scripts\Activate.ps1"
python discord_router.py
