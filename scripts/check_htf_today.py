#!/usr/bin/env python3
"""
scripts/check_htf_today.py — redteam-htf-review precheck
今日 HTF_CONTEXT 存在才觸發 REDTEAM 盲審；否則 SKIP（節省 opus 額度）。

用法（Router precheck）：
    python scripts/check_htf_today.py
    → 輸出 "SKIP: ..." 則 Router 不觸發；無輸出或 exit 0 則繼續
"""
from __future__ import annotations

import sqlite3
import sys
from datetime import date
from pathlib import Path

import td_console  # noqa: F401  Windows cp950 console fix

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "tradedesk.db"


def main() -> int:
    today = date.today().isoformat()

    if not DB.exists():
        print(f"SKIP: 資料庫不存在（{DB}），尚未完成建置")
        return 0

    try:
        con = sqlite3.connect(str(DB))
        (count,) = con.execute(
            "SELECT COUNT(*) FROM htf_context WHERE date = ?", (today,)
        ).fetchone()
        con.close()
    except sqlite3.OperationalError as e:
        print(f"SKIP: htf_context 表查詢失敗（{e}），可能尚未初始化")
        return 0

    if count == 0:
        print(f"SKIP: 今日（{today}）無 HTF_CONTEXT，chart-htf 尚未完成")
        return 0

    # 有資料 → 不輸出 SKIP → Router 正常觸發 redteam-htf-review
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
