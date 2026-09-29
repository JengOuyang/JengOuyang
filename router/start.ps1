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
# requirements.txt 有新套件時 git pull 後必須重跑 pip install；
# 在這裡自動同步，避免忘記導致 cron 任務啟動失敗（BUG_20260926_0710、BUG_20260929_1820）。
$pip = Join-Path $root ".venv\Scripts\pip.exe"
if (Test-Path $pip) { & $pip install --quiet -r (Join-Path $root "requirements.txt") }
& $venv router\discord_router.py
