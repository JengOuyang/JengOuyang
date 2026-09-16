# start.ps1 — 手動啟動 Router（第一次測試用）
# 路徑由這支腳本自己的位置推出來，不寫死——原本寫死成 C:\trade-desk，
# 而實際資料夾可能叫 C:\trade_desk（底線），一個字元的差別就整支跑不起來。
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$venv = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venv)) {
    Write-Error "找不到 $venv —— 先建立虛擬環境：python -m venv .venv"
    exit 1
}
& $venv router\discord_router.py
