#!/usr/bin/env python3
"""merkle_anchor.py — 每日 Merkle 錨點（LEDGER）

每天 00:05 UTC 由 ledger-anchor 排程呼叫。
對前一天（UTC）每個業務表的 row_hash 列表計算 Merkle root，
透過 LEDGER ingest API 寫入 audit_anchor，並輸出 AUDIT_ANCHOR JSON。

用法：
    python scripts/merkle_anchor.py
    python scripts/merkle_anchor.py --date 2026-09-22   # 指定日期
    python scripts/merkle_anchor.py --dry-run           # 只算不寫
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import td_console  # noqa: F401  (Windows cp950 console fix)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "tradedesk.db"

# 業務表（排除 audit_anchor 本身與 corrections）
TABLES = [
    "ohlcv", "funding", "oi", "orderbook_snap", "indicators",
    "macro_brief", "htf_context", "trade_plan", "risk_decision",
    "orders", "fills", "positions", "equity_curve",
    "trade_journal", "agent_heartbeat", "tasks", "config_versions",
    "universe", "content", "ig_insights",
    "bug_reports", "fix_log", "llm_usage",
]


def sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def merkle_root(hashes: list[str]) -> str:
    """標準二元 Merkle tree；空列表回傳 64 個零。"""
    if not hashes:
        return "0" * 64
    layer = list(hashes)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])  # 奇數補重複末項
        layer = [sha256_hex(layer[i] + layer[i + 1]) for i in range(0, len(layer), 2)]
    return layer[0]


def day_ts_range(date_str: str) -> tuple[int, int]:
    d = dt.date.fromisoformat(date_str)
    start = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
    return start, start + 86400


def query_table(
    conn: sqlite3.Connection, table: str, start_ts: int, end_ts: int
) -> tuple[int, list[str]]:
    try:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE ingest_ts >= ? AND ingest_ts < ?",
            (start_ts, end_ts),
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT row_hash FROM {table}"
            " WHERE ingest_ts >= ? AND ingest_ts < ? ORDER BY row_id",
            (start_ts, end_ts),
        ).fetchall()
        hashes = [r[0] for r in rows if r[0]]
        return count, hashes
    except sqlite3.OperationalError:
        return 0, []


def post_ingest(payload: dict, port: str, token: str) -> dict:
    url = f"http://127.0.0.1:{port}/ingest/audit_anchor"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json; charset=utf-8",
                 "X-Writer-Token": token},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"ingest HTTP {e.code}: {e.read().decode('utf-8', errors='replace')}"
        ) from e
    except OSError as e:
        raise RuntimeError(f"無法連接 ingest server（{url}）：{e}") from e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD UTC，預設為昨天")
    ap.add_argument("--dry-run", action="store_true", help="只計算不寫入 ingest")
    a = ap.parse_args()

    date_str = a.date or (
        dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    ).isoformat()

    if not DB_PATH.exists():
        print(json.dumps({"error": f"資料庫不存在：{DB_PATH}"}, ensure_ascii=False))
        return 1

    start_ts, end_ts = day_ts_range(date_str)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA query_only = 1")

    results: dict[str, dict] = {}
    for table in TABLES:
        count, hashes = query_table(conn, table, start_ts, end_ts)
        results[table] = {"row_count": count, "merkle_root": merkle_root(hashes)}
    conn.close()

    combined_root = merkle_root([results[t]["merkle_root"] for t in TABLES])
    now_ts = int(time.time())
    errors: list[str] = []

    if not a.dry_run:
        token = os.environ.get("INGEST_TOKEN_LEDGER", "")
        port = os.environ.get("INGEST_PORT", "8787")
        if not token:
            print(json.dumps(
                {"error": "INGEST_TOKEN_LEDGER 未設定，請在 router/.env 補上"},
                ensure_ascii=False,
            ))
            return 1
        for table in TABLES:
            try:
                post_ingest(
                    {
                        "date": date_str,
                        "table_name": table,
                        "row_count": results[table]["row_count"],
                        "merkle_root": results[table]["merkle_root"],
                        "discord_msg_id": None,
                        "ingest_ts": now_ts,
                        "writer": "merkle_anchor",
                    },
                    port, token,
                )
            except RuntimeError as e:
                errors.append(f"{table}: {e}")

    msg = {
        "msg_type": "AUDIT_ANCHOR",
        "from": "LEDGER",
        "to": [],
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload": {
            "date": date_str,
            "merkle_root": combined_root,
            "row_counts": {t: results[t]["row_count"] for t in TABLES},
            "total_rows": sum(v["row_count"] for v in results.values()),
            "errors": errors,
            "dry_run": a.dry_run,
        },
    }
    print(json.dumps(msg, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
