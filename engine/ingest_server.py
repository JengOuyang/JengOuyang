#!/usr/bin/env python3
"""
engine/ingest_server.py — 唯一資料倉寫入口

POST http://127.0.0.1:8787/ingest/<table>
Header: X-Writer-Token: <token>
Body:   JSON object（業務欄位）
回傳:   {"row_id": int, "row_hash": str}

非法 token → 401
表名不合法  → 400
寫入衝突    → 409（UNIQUE constraint）
其他 DB 錯誤 → 400
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]

# td_console 在 scripts/，需先加入 sys.path
import sys as _sys
_scripts = ROOT / "scripts"
if str(_scripts) not in _sys.path:
    _sys.path.insert(0, str(_scripts))
import td_console  # noqa: F401  Windows cp950 console fix
DB = ROOT / "data" / "tradedesk.db"
PORT = 8787

# 基礎設施欄位（與 verify_chain.py 保持一致）
_INFRA_COLS = frozenset({"row_id", "ingest_ts", "writer", "prev_hash", "row_hash"})

# Writer token → writer name（從 env 載入）
_TOKEN_MAP: dict[str, str] = {}

def _reload_tokens() -> None:
    _TOKEN_MAP.clear()
    for k, v in os.environ.items():
        if k.startswith("INGEST_TOKEN_") and v:
            writer = k.removeprefix("INGEST_TOKEN_").lower()
            _TOKEN_MAP[v] = writer

_reload_tokens()


def canonical_json(d: dict) -> str:
    """鍵排序、無空白、UTF-8（與 verify_chain.py 保持一致）。"""
    return json.dumps(d, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_sql_default(dflt_value) -> object:
    """SQLite PRAGMA dflt_value 字串 → Python 值。"""
    if dflt_value is None:
        return None
    s = str(dflt_value).strip()
    if s.upper() == "NULL":
        return None
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    return s


def _get_biz_row(con: sqlite3.Connection, table: str, payload: dict) -> dict:
    """從 PRAGMA 讀取業務欄位清單，以 payload 為主、schema 預設值補齊。
    與 verify_chain.py 的 get_biz_cols() + biz_dict 邏輯完全對齊。"""
    pragma = con.execute(f"PRAGMA table_info({table})").fetchall()
    biz_row = {}
    for row in pragma:
        col = row[1]
        if col in _INFRA_COLS:
            continue
        biz_row[col] = payload.get(col, _parse_sql_default(row[4]))
    return biz_row


def _get_prev_hash(con: sqlite3.Connection, table: str) -> str:
    try:
        row = con.execute(
            f"SELECT row_hash FROM [{table}] ORDER BY row_id DESC LIMIT 1"
        ).fetchone()
        return row[0] if (row and row[0]) else ""
    except sqlite3.OperationalError:
        return ""


def ingest(table: str, payload: dict, writer: str) -> tuple[int, str]:
    """寫入一列並回傳 (row_id, row_hash)。"""
    con = sqlite3.connect(str(DB))
    try:
        prev_hash = _get_prev_hash(con, table)
        now = int(time.time())

        # 從 schema 補齊所有業務欄位預設值，與 verify_chain.py 讀回邏輯一致
        biz_row = _get_biz_row(con, table, payload)
        row_hash = hashlib.sha256(
            (prev_hash + canonical_json(biz_row)).encode("utf-8")
        ).hexdigest()

        row = dict(payload)
        row["ingest_ts"] = now
        row["writer"] = writer
        row["prev_hash"] = prev_hash
        row["row_hash"] = row_hash

        cols = ", ".join(f"[{c}]" for c in row)
        placeholders = ", ".join("?" for _ in row)
        con.execute(
            f"INSERT INTO [{table}] ({cols}) VALUES ({placeholders})",
            list(row.values()),
        )
        con.commit()

        inserted = con.execute(
            f"SELECT row_id FROM [{table}] WHERE row_hash = ?", (row_hash,)
        ).fetchone()
        return inserted[0], row_hash
    finally:
        con.close()


class IngestHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # 關閉預設 access log
        pass

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if not path.startswith("/ingest/"):
            self._reply(404, {"error": "not found"})
            return

        table = path[len("/ingest/"):]
        if not table or not table.replace("_", "").isalnum():
            self._reply(400, {"error": "invalid table name"})
            return

        token = self.headers.get("X-Writer-Token", "")
        writer = _TOKEN_MAP.get(token)
        if not writer:
            self._reply(401, {"error": "unauthorized"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, ValueError):
            self._reply(400, {"error": "invalid json"})
            return

        if not isinstance(payload, dict):
            self._reply(400, {"error": "payload must be a json object"})
            return

        try:
            row_id, row_hash = ingest(table, payload, writer)
            self._reply(200, {"row_id": row_id, "row_hash": row_hash})
        except sqlite3.IntegrityError as e:
            self._reply(409, {"error": str(e)})
        except sqlite3.OperationalError as e:
            self._reply(400, {"error": str(e)})
        except Exception as e:
            self._reply(500, {"error": str(e)})

    def _reply(self, status: int, body: dict) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    if not DB.exists():
        print(f"[ingest_server] 警告：資料庫不存在（{DB}），啟動後等待第一次 POST 時才會報錯")
    server = HTTPServer(("127.0.0.1", PORT), IngestHandler)
    print(f"[ingest_server] 啟動 http://127.0.0.1:{PORT} — 已載入 {len(_TOKEN_MAP)} 個 writer token")
    server.serve_forever()


if __name__ == "__main__":
    main()
