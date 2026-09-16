@echo off
REM Checkpoint commit before you start changing things.
REM Usage: snapshot.cmd fixing the router scheduler
REM
REM It does two things:
REM   1. git commit (--no-verify: this is a local save point, not something you push)
REM   2. refresh the guard_paths baseline
REM
REM Step 2 matters when the Router is running. After every agent call the Router runs
REM `guard_paths verify --agent <id> --restore`, which git-checkouts any protected file
REM that changed outside that agent authority. Your edits look exactly like that.
REM Committing makes the checkout a no-op; re-snapshotting stops the false alarms.
REM ASCII-only + CRLF on purpose (see dev.cmd for why).
cd /d %~dp0\..
set MSG=%*
if "%MSG%"=="" set MSG=checkpoint
set PY=python
if exist .venv\Scripts\python.exe set PY=.venv\Scripts\python.exe
git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
  echo Not a git repository yet. Run: git init -b main
  echo See docs/DAY0_RUNBOOK.md step 3B.
  exit /b 1
)
git add -A
git diff --cached --quiet && echo Nothing to save ^(no changes^) && goto :guard
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
:guard
if exist router\guard_state.json %PY% scripts\guard_paths.py snapshot >nul && echo Guard baseline refreshed
