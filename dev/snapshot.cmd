@echo off
REM Checkpoint commit before you start changing things.
REM Usage: snapshot.cmd fixing the router scheduler
REM
REM --no-verify is deliberate: this is a local save point, not something you push.
REM ASCII-only + CRLF on purpose (see dev.cmd for why).
cd /d %~dp0\..
set MSG=%*
if "%MSG%"=="" set MSG=checkpoint
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
  echo Not a git repository yet. Run: git init -b main
  echo See docs/DAY0_RUNBOOK.md step 3B.
  exit /b 1
)
git add -A
git diff --cached --quiet && echo Nothing to save ^(no changes^) && exit /b 0
git commit -q --no-verify -m "checkpoint: %MSG%"
if errorlevel 1 (
  echo.
  echo Commit failed - read the git message above.
  echo If it says "Author identity unknown", run these once:
  echo   git config --global user.name "Blacksheep"
  echo   git config --global user.email "your@email"
  exit /b 1
)
echo Saved: %MSG%
