#!/usr/bin/env python3
"""td_proc.py — 呼叫子程序的唯一入口（Windows cp950 會在這裡咬人）。

為什麼需要它：
    `subprocess.run(..., text=True)` 不指定 encoding 時，Python 用**系統地區編碼**解碼。
    Windows 繁中是 cp950，而我們的腳本輸出是 UTF-8 中文——讀取執行緒會直接炸掉：

        Exception in thread Thread-1 (_readerthread):
          File "...subprocess.py", line 1614, in _readerthread
            buffer.append(fh.read())
        UnicodeDecodeError: 'cp950' codec can't decode byte 0x8a ...

    最陰險的是**主程式看起來還是成功的**：例外發生在讀取執行緒，主程式拿到空字串、
    returncode 仍是 0，於是 preflight 印出「OK」。真的失敗時你會得到一個空的錯誤訊息。

    v3.0.5 在 lint 修過一次，但只修了那一支。這支程式是「一次修完，而且回不去」的版本，
    lint 第 29 項禁止任何地方再直接用 `subprocess.run(text=True)` 而不指定編碼。

用法：
    from td_proc import run, run_text
    r = run(["git", "status"])          # 回傳 CompletedProcess，stdout/stderr 已是 str
    rc, out, err = run_text(["git", "status"])
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

__all__ = ["run", "run_text", "child_env"]


def child_env(extra: dict | None = None) -> dict:
    """子程序環境：強制它用 UTF-8 輸出，這樣我們這端才解得開。"""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    if extra:
        env.update(extra)
    return env


def run(cmd, *, cwd: Path | str | None = None, timeout: float | None = None,
        input: str | None = None, env: dict | None = None,
        check: bool = False) -> subprocess.CompletedProcess:
    """跑一個子程序並以 UTF-8 取回文字輸出。永遠不會因為編碼而丟例外。"""
    return subprocess.run(
        cmd, cwd=cwd, timeout=timeout, input=input, check=check,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",      # ← 這兩個就是重點
        env=child_env(env),
    )


def run_text(cmd, **kw) -> tuple[int | None, str, str]:
    """同 run()，但回傳 (returncode, stdout, stderr)；逾時回 (None, "", "timeout")。"""
    try:
        r = run(cmd, **kw)
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return None, "", "timeout"
    except FileNotFoundError:
        return -1, "", "not found"
