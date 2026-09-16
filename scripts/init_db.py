#!/usr/bin/env python3
"""init_db.py — 建立資料倉（表 + 視圖）。可重複執行（IF NOT EXISTS）。"""
import sqlite3, sys
from pathlib import Path

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "tradedesk.db"
DB.parent.mkdir(parents=True, exist_ok=True)
con = sqlite3.connect(DB)
for f in ("001_schema.sql", "002_views.sql"):
    con.executescript((ROOT / "db" / f).read_text(encoding="utf-8"))
    print(f"  已套用 db/{f}")
for f in sorted((ROOT / "db" / "migrations").glob("*.sql")):
    con.executescript(f.read_text(encoding="utf-8")); print(f"  已套用 migrations/{f.name}")
t = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
v = con.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='view'").fetchone()[0]
con.commit(); con.close()
print(f"完成：{DB} （{t} 個表、{v} 個視圖）")
