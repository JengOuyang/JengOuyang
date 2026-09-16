# watchdog.ps1 — 由 Windows 工作排程器每 5 分鐘執行；Router 不在就重啟
$root = Split-Path -Parent $PSScriptRoot   # 不寫死：資料夾名稱可能是 trade_desk 或別的
$running = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*discord_router.py*" }
if (-not $running) {
  Start-Process -FilePath "$root\.venv\Scripts\python.exe" -ArgumentList "$root\router\discord_router.py" -WorkingDirectory "$root\router" -WindowStyle Hidden
  Add-Content "$root\logs\watchdog.log" "$(Get-Date -Format s) restarted router"
}
