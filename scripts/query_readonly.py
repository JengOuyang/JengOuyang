#!/usr/bin/env python3
"""
query_readonly.py — LLM Agent 查詢資料倉的唯一入口。

用法（Agent 在自己的目錄下執行）：
    python ../../scripts/query_readonly.py "SELECT * FROM v_market WHERE symbol='BTCUSDT' LIMIT 20"

三層防護：
  1. 只接受 SELECT / WITH 開頭的敘述，單一敘述（無分號串接）。
  2. 連線以 mode=ro 開啟並設 PRAGMA query_only=1。
  3. 語句中出現的每個資料來源都必須在該 Agent 的視圖授權清單內
     （shared/view_grants.yaml）——查底層資料表一律拒絕。

Agent 身分：優先取環境變數 TD_AGENT（Router 設定），否則取工作目錄名稱。
"""
from __future__ import annotations
import json, os, re, sqlite3, sys
from pathlib import Path

import yaml

import td_console  # noqa: F401  （Windows cp950 主控台會讓 print 中文/符號崩潰）

ROOT = Path(__file__).resolve().parents[1]
DB = Path(os.environ.get("TD_DB", ROOT / "data" / "tradedesk.db"))
GRANTS = yaml.safe_load((ROOT / "shared" / "view_grants.yaml").read_text(encoding="utf-8"))

SQL_START = re.compile(r"^\s*(select|with)\b", re.I)
# 抓出 FROM / JOIN 後面的識別字（忽略子查詢的左括號）
SRC = re.compile(r"\b(?:from|join)\s+([A-Za-z_][A-Za-z0-9_]*)", re.I)
BANNED = re.compile(r"\b(attach|pragma|insert|update|delete|drop|create|alter|replace|vacuum)\b", re.I)


def agent_id() -> str:
    return os.environ.get("TD_AGENT") or Path.cwd().name


def allowed_views(aid: str) -> set[str]:
    return set(GRANTS.get("common", [])) | set(GRANTS.get("grants", {}).get(aid, []))


def fail(msg: str, **extra):
    print(json.dumps({"error": msg, **extra}, ensure_ascii=False))
    raise SystemExit(1)


def main() -> int:
    sql = " ".join(sys.argv[1:]).strip().rstrip(";")
    if not sql:
        fail("用法：query_readonly.py \"<SELECT ...>\"")
    aid = agent_id()
    allowed = allowed_views(aid)
    if not allowed:
        fail(f"沒有任何視圖授權給 agent '{aid}'，請確認執行目錄或 TD_AGENT 是否正確")
    if not SQL_START.match(sql):
        fail("只允許 SELECT / WITH 開頭的查詢")
    if ";" in sql:
        fail("只允許單一敘述（不可用分號串接）")
    if BANNED.search(sql):
        fail("查詢中包含被禁止的關鍵字")

    used = {m.lower() for m in SRC.findall(sql)}
    # CTE 名稱（WITH x AS (...)）不算資料來源
    ctes = {m.lower() for m in re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s+as\s*\(", sql, re.I)}
    illegal = sorted(v for v in used - ctes if v not in {a.lower() for a in allowed})
    if illegal:
        fail(
            f"agent '{aid}' 未被授權存取：{', '.join(illegal)}",
            allowed_views=sorted(allowed),
            hint="只能查視圖，不能查底層資料表；需要新視圖請發 SKILL_REQUEST 給 FORGE",
        )

    if not DB.exists():
        fail(f"資料庫尚未建立：{DB}（請先執行 python scripts/init_db.py）", agent=aid, allowed_views=sorted(allowed))

    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.execute("PRAGMA query_only=1")
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute(sql).fetchmany(500)]
    except sqlite3.Error as e:
        fail(f"SQL 錯誤：{e}")
    print(json.dumps({"agent": aid, "rows": rows, "count": len(rows),
                      "truncated": len(rows) == 500}, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
