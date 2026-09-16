@echo off
REM TRADE-DESK development session launcher.
REM
REM Start from dev\ on purpose (ADR-004): the project root has no CLAUDE.md,
REM so dev\ and agents\ are sibling inheritance chains and your developer
REM instructions never leak into the 15 agents.
REM
REM --add-dir .. is required: Claude Code scopes file access to the startup
REM directory, so a session launched in dev\ cannot read ..\engine, ..\scripts
REM or ..\tests without it.
REM
REM This file is ASCII-only and CRLF on purpose. cmd.exe reads .cmd files in the
REM console ANSI codepage (cp950 here), so UTF-8 Chinese comments get mangled and
REM the parser swallows the next characters. See docs/04_DEV_ENVIRONMENT.md.
cd /d %~dp0
call ..\.venv\Scripts\activate.bat 2>nul
claude --add-dir .. %*
