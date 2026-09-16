#!/usr/bin/env python3
"""
task_db.py — ceo-task-sweep 的 precheck。

輸出（Router precheck 約定）：
  SKIP  ...  → 無待處理任務，不觸發 LLM（省額度）
  READY ...  → 有待審核或逾期任務，觸發 CEO 處理

「待處理」的定義：
  - status IN ('REVIEW')：等 CEO 審核
  - status IN ('ASSIGNED','IN_PROGRESS') 且 ts < 現在 - 2h：可能超時
  - status = 'NEW'：尚未派工

用法（在任意目錄）：
    python scripts/task_db.py --precheck
"""
from __future__ import annotations
import argparse, os, sqlite3, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台中文符號防崩）

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("TD_DB", ROOT / "data" / "tradedesk.db"))

OVERDUE_HOURS = 2


def _pending(con: sqlite3.Connection) -> list[tuple]:
    cutoff = int((datetime.now(timezone.utc) - timedelta(hours=OVERDUE_HOURS)).timestamp())
    return con.execute(
        """
        SELECT task_id, assignee, status, ts
        FROM tasks
        WHERE status IN ('NEW','REVIEW')
           OR (status IN ('ASSIGNED','IN_PROGRESS') AND ts < ?)
        ORDER BY ts ASC
        LIMIT 20
        """,
        (cutoff,),
    ).fetchall()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--precheck", action="store_true")
    args = parser.parse_args()

    if not args.precheck:
        parser.print_help()
        return 1

    if not DB.exists():
        print("SKIP 資料庫尚未初始化")
        return 0

    try:
        con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
        rows = _pending(con)
        con.close()
    except sqlite3.OperationalError as exc:
        # tasks 表尚未建立（建置期）
        print(f"SKIP {exc}")
        return 0

    if not rows:
        print("SKIP 無待處理任務")
        return 0

    review = [r for r in rows if r[2] == "REVIEW"]
    new = [r for r in rows if r[2] == "NEW"]
    overdue = [r for r in rows if r[2] in ("ASSIGNED", "IN_PROGRESS")]

    parts = []
    if review:
        parts.append(f"{len(review)} 件待審核")
    if new:
        parts.append(f"{len(new)} 件未派工")
    if overdue:
        parts.append(f"{len(overdue)} 件超時 >={OVERDUE_HOURS}h")
    print(f"READY {' · '.join(parts)}（共 {len(rows)} 件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
