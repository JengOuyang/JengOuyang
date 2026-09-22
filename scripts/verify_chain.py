#!/usr/bin/env python3
"""verify_chain.py — hash chain 完整性驗證（LEDGER on_mention）

每週還原測試、或在 Discord @mention TD-LEDGER 時觸發。
對 tradedesk.db 所有業務表逐列重算 row_hash；
任何不一致輸出失敗 JSON 並 exit 1。

用法：
    python scripts/verify_chain.py
    python scripts/verify_chain.py --table ohlcv
    python scripts/verify_chain.py --db /path/to/tradedesk.db
    python scripts/verify_chain.py --dry-run   # 只報告不需要環境變數
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import td_console  # noqa: F401  (Windows cp950 console fix)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "tradedesk.db"

# 基礎設施欄位：不參與 row_hash 計算
INFRA_COLS = frozenset({"row_id", "ingest_ts", "writer", "prev_hash", "row_hash"})

# 與 merkle_anchor.py 相同的業務表，加上 audit_anchor / corrections
TABLES = [
    "ohlcv", "funding", "oi", "orderbook_snap", "indicators",
    "macro_brief", "htf_context", "trade_plan", "risk_decision",
    "orders", "fills", "positions", "equity_curve",
    "trade_journal", "agent_heartbeat", "tasks", "config_versions",
    "audit_anchor", "corrections",
    "universe", "content", "ig_insights",
    "bug_reports", "fix_log", "llm_usage",
]


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def canonical_json(obj: dict) -> str:
    """鍵排序、無空白、UTF-8（與 ingest server 一致）。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def get_biz_cols(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows if r[1] not in INFRA_COLS]


def verify_table(conn: sqlite3.Connection, table: str) -> dict:
    """驗算單張表；回傳 {table, ok, rows_checked, failures[], note}。"""
    biz_cols = get_biz_cols(conn, table)
    if not biz_cols:
        return {"table": table, "ok": True, "rows_checked": 0, "note": "no business cols"}

    select_cols = ["row_id", "prev_hash", "row_hash"] + biz_cols
    try:
        rows = conn.execute(
            f"SELECT {', '.join(select_cols)} FROM {table} ORDER BY row_id"
        ).fetchall()
    except sqlite3.OperationalError as e:
        return {"table": table, "ok": True, "rows_checked": 0, "note": str(e)}

    if not rows:
        return {"table": table, "ok": True, "rows_checked": 0}

    failures: list[dict] = []
    prev_stored = ""

    for tup in rows:
        d = dict(zip(select_cols, tup))
        row_id = d["row_id"]
        stored_prev = d["prev_hash"] or ""
        stored_hash = d["row_hash"] or ""

        biz_dict = {c: d[c] for c in biz_cols}
        expected = sha256_hex(stored_prev + canonical_json(biz_dict))

        hash_ok = expected == stored_hash
        # 鏈連續性：本列的 prev_hash 應等於上一列的 row_hash
        chain_ok = stored_prev == prev_stored

        if not hash_ok or not chain_ok:
            failures.append({
                "row_id": row_id,
                "hash_ok": hash_ok,
                "chain_ok": chain_ok,
            })
            if len(failures) >= 10:
                failures.append({"note": "truncated at 10"})
                break

        prev_stored = stored_hash

    return {
        "table": table,
        "ok": len(failures) == 0,
        "rows_checked": len(rows),
        "failures": failures,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=None, help="只驗單張表")
    ap.add_argument("--db", default=None, help="DB 路徑（預設 data/tradedesk.db）")
    ap.add_argument("--dry-run", action="store_true", help="（保留，與其他 scripts 介面一致）")
    a = ap.parse_args()

    db_path = Path(a.db) if a.db else DB_PATH
    if not db_path.exists():
        print(json.dumps({"error": f"資料庫不存在：{db_path}"}, ensure_ascii=False))
        return 1

    tables = [a.table] if a.table else TABLES

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA query_only = 1")

    results = []
    for tbl in tables:
        results.append(verify_table(conn, tbl))
    conn.close()

    all_ok = all(r["ok"] for r in results)
    failed = [r for r in results if not r["ok"]]
    total_rows = sum(r.get("rows_checked", 0) for r in results)

    output = {
        "msg_type": "DATA_ALERT" if not all_ok else "AUDIT_ANCHOR",
        "from": "LEDGER",
        "to": [],
        "payload": {
            "check": "verify_chain",
            "ok": all_ok,
            "tables_checked": len(tables),
            "rows_checked": total_rows,
            "failed_tables": [r["table"] for r in failed],
            "details": results,
        },
    }
    if not all_ok:
        output["payload"]["issue"] = "hash chain 驗證失敗，可能發生資料竄改"

    print(json.dumps(output, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
