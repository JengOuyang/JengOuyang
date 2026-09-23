#!/usr/bin/env python3
"""crosscheck.py — FEED 雙源交叉驗證（LEDGER，每日 00:10 UTC）

只讀資料倉內 FEED 已寫入的兩個 source（bitget / binance），
不對外部 API 發任何請求。
對前一天（UTC）1H 收盤進行交叉驗證，差距 > 0.5% 的列標 SUSPECT=1。

用法：
    python scripts/crosscheck.py
    python scripts/crosscheck.py --date 2026-09-22
    python scripts/crosscheck.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import sys
import time
from pathlib import Path

import td_console  # noqa: F401  (Windows cp950 console fix)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "tradedesk.db"

SOURCE_A = "bitget"
SOURCE_B = "binance"
TF = "1H"
THRESHOLD = 0.005  # 0.5%


def day_ts_range(date_str: str) -> tuple[int, int]:
    d = dt.date.fromisoformat(date_str)
    start = int(dt.datetime(d.year, d.month, d.day, tzinfo=dt.timezone.utc).timestamp())
    return start, start + 86400


def find_suspects(
    conn: sqlite3.Connection, start_ts: int, end_ts: int
) -> list[dict]:
    """回傳所有差距超過 THRESHOLD 的 (symbol, ts, row_id_a, row_id_b, c_a, c_b, diff_pct)。"""
    rows = conn.execute(
        """
        SELECT
            a.symbol,
            a.ts,
            a.row_id  AS row_id_a,
            b.row_id  AS row_id_b,
            a.c       AS c_a,
            b.c       AS c_b,
            CASE WHEN b.c != 0
                 THEN ABS(a.c - b.c) / b.c
                 ELSE NULL
            END AS diff_pct
        FROM ohlcv a
        JOIN ohlcv b
          ON a.symbol = b.symbol
         AND a.ts     = b.ts
         AND b.source = ?
         AND b.tf     = ?
         AND b.ingest_ts >= ? AND b.ingest_ts < ?
         AND b.suspect = 0
        WHERE a.source  = ?
          AND a.tf      = ?
          AND a.ingest_ts >= ? AND a.ingest_ts < ?
          AND a.suspect = 0
          AND ABS(a.c - b.c) / NULLIF(b.c, 0) > ?
        ORDER BY a.symbol, a.ts
        """,
        (
            SOURCE_B, TF, start_ts, end_ts,
            SOURCE_A, TF, start_ts, end_ts,
            THRESHOLD,
        ),
    ).fetchall()
    return [
        {
            "symbol": r[0],
            "ts": r[1],
            "row_id_a": r[2],
            "row_id_b": r[3],
            "c_a": r[4],
            "c_b": r[5],
            "diff_pct": round(r[6] * 100, 4) if r[6] is not None else None,
        }
        for r in rows
    ]


def mark_suspect(conn: sqlite3.Connection, row_ids: list[int]) -> None:
    """直接 UPDATE suspect=1（suspect 不納入 row_hash，是驗證旗標）。"""
    if not row_ids:
        return
    placeholders = ",".join("?" * len(row_ids))
    conn.execute(
        f"UPDATE ohlcv SET suspect = 1 WHERE row_id IN ({placeholders})",
        row_ids,
    )
    conn.commit()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None, help="YYYY-MM-DD UTC，預設為昨天")
    ap.add_argument("--dry-run", action="store_true", help="只計算不寫入")
    a = ap.parse_args()

    date_str = a.date or (
        dt.datetime.now(dt.timezone.utc).date() - dt.timedelta(days=1)
    ).isoformat()

    if not DB_PATH.exists():
        print(json.dumps(
            {"error": f"資料庫不存在：{DB_PATH}"}, ensure_ascii=False
        ))
        return 1

    start_ts, end_ts = day_ts_range(date_str)

    conn = sqlite3.connect(str(DB_PATH))
    try:
        suspects = find_suspects(conn, start_ts, end_ts)

        if not a.dry_run and suspects:
            all_ids = [s["row_id_a"] for s in suspects] + [s["row_id_b"] for s in suspects]
            mark_suspect(conn, all_ids)
    except sqlite3.OperationalError as e:
        print(json.dumps({"error": f"DB 查詢失敗：{e}"}, ensure_ascii=False))
        return 1
    finally:
        conn.close()

    msg = {
        "msg_type": "DATA_ALERT" if suspects else "INFO",
        "from": "LEDGER",
        "to": ["LEDGER", "WATCH"] if suspects else [],
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "payload": {
            "date": date_str,
            "crosscheck": {
                "source_a": SOURCE_A,
                "source_b": SOURCE_B,
                "tf": TF,
                "threshold_pct": THRESHOLD * 100,
                "suspect_count": len(suspects),
                "marked_dry_run": a.dry_run,
                "suspects": suspects,
            },
        },
    }
    if suspects:
        msg["payload"]["table"] = "ohlcv"
        msg["payload"]["issue"] = (
            f"{len(suspects)} 筆 {TF} 收盤差距 > {THRESHOLD*100}%"
            f"（{SOURCE_A} vs {SOURCE_B}），已標 SUSPECT"
            + ("（dry-run，未寫入）" if a.dry_run else "")
        )
        msg["payload"]["affected_range"] = date_str

    print(json.dumps(msg, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
