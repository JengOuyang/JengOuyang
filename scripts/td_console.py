#!/usr/bin/env python3
"""td_console.py — 讓所有腳本在 Windows 主控台也能印中文與符號。

為什麼需要它：
    Windows 的 PowerShell 預設用 cp950（繁中）或 cp936（簡中）編碼。
    腳本只要 print 一個 `⚠️`，Python 就會丟 UnicodeEncodeError 並**直接崩潰**。
    更糟的是：被 subprocess 呼叫時，崩潰訊息跑到 stderr，而呼叫端只看 stdout，
    於是使用者看到的是「ERROR [19] 隔離驗證失敗：」後面**一片空白**。

    真實案例（v3.0.5 修掉的）：
        (.venv) PS C:\\trade_desk> python scripts\\lint_agents.py
        lint: 15 個 Agent、39 個 skill、45 個排程
          ERROR [19] 隔離驗證失敗：      ← 後面什麼都沒有

用法：每支會印非 ASCII 的腳本在 import 區塊放一行 `import td_console  # noqa: F401`。
      lint 第 26 項會強制這件事。

它只改「這個 Python 行程自己的輸出編碼」，不動系統設定、不動主控台代碼頁。
"""
from __future__ import annotations

import io
import sys


def _force_utf8() -> None:
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        enc = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
        if enc == "utf8":
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")   # Python 3.7+
        except Exception:
            try:                                                     # 極少數被包裝過的情況
                setattr(sys, name, io.TextIOWrapper(
                    stream.buffer, encoding="utf-8", errors="replace", line_buffering=True))
            except Exception:
                pass          # 連包裝都失敗就算了——不要因為印字而讓主要工作掛掉


_force_utf8()
