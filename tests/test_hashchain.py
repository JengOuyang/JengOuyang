"""
tests/test_hashchain.py — engine/ingest_server.py 驗收測試
T-2026-0923-009

驗收條件：
  1. 正常寫入兩筆，hash chain 連鎖正確（row2.prev_hash == row1.row_hash）
  2. 非法 token → 401，不寫入任何資料
  3. 寫入後 verify_chain.py 驗通（breaks == 0）
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
# engine/ 沒有 __init__.py，直接把目錄加進 sys.path 再 import
if str(ROOT / "engine") not in sys.path:
    sys.path.insert(0, str(ROOT / "engine"))
# td_console 在 scripts/，ingest_server 需要它
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

_TEST_PORT = 18787  # 避免與正式 server port 8787 衝突
_VALID_TOKEN = "test-token-feed-001"


def _build_test_db(path: Path) -> None:
    schema = (ROOT / "db" / "001_schema.sql").read_text(encoding="utf-8")
    con = sqlite3.connect(str(path))
    con.executescript(schema)
    con.close()


@pytest.fixture(scope="module")
def running_server(tmp_path_factory):
    """建立隔離 DB，啟動 ingest_server，yield 環境，完成後關閉。"""
    import ingest_server as srv  # engine/ 已在 sys.path

    tmp = tmp_path_factory.mktemp("ingest_test")
    db_path = tmp / "tradedesk.db"
    _build_test_db(db_path)

    # patch 模組級變數（不影響其他 test session）
    orig_db = srv.DB
    orig_port = srv.PORT
    orig_map = dict(srv._TOKEN_MAP)

    srv.DB = db_path
    srv.PORT = _TEST_PORT
    srv._TOKEN_MAP.clear()
    srv._TOKEN_MAP[_VALID_TOKEN] = "feed"

    httpd = srv.HTTPServer(("127.0.0.1", _TEST_PORT), srv.IngestHandler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.15)  # 等伺服器就緒

    yield {"db": db_path, "url": f"http://127.0.0.1:{_TEST_PORT}"}

    httpd.shutdown()
    srv.DB = orig_db
    srv.PORT = orig_port
    srv._TOKEN_MAP.clear()
    srv._TOKEN_MAP.update(orig_map)


def _post(url: str, table: str, payload: dict, token: str = _VALID_TOKEN):
    import urllib.request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{url}/ingest/{table}",
        data=data,
        headers={"X-Writer-Token": token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except Exception as e:
        # urllib raises HTTPError for 4xx/5xx
        import urllib.error
        if isinstance(e, urllib.error.HTTPError):
            return e.code, json.loads(e.read())
        raise


def test_normal_write_and_chain(running_server):
    """正常寫入兩筆，驗 prev_hash 連鎖。"""
    url = running_server["url"]
    db = running_server["db"]

    status1, d1 = _post(url, "ohlcv", {
        "symbol": "BTC_USDT", "tf": "1h", "ts": 1700000000,
        "o": 30000.0, "h": 31000.0, "l": 29500.0, "c": 30500.0,
        "v": 100.0, "quote_v": 3050000.0, "source": "test",
    })
    assert status1 == 200, f"第一筆寫入失敗：{d1}"
    assert "row_id" in d1 and "row_hash" in d1

    status2, d2 = _post(url, "ohlcv", {
        "symbol": "BTC_USDT", "tf": "1h", "ts": 1700003600,
        "o": 30500.0, "h": 31500.0, "l": 30000.0, "c": 31000.0,
        "v": 120.0, "quote_v": 3720000.0, "source": "test",
    })
    assert status2 == 200, f"第二筆寫入失敗：{d2}"

    con = sqlite3.connect(str(db))
    rows = con.execute(
        "SELECT row_hash, prev_hash FROM ohlcv ORDER BY row_id"
    ).fetchall()
    con.close()

    assert len(rows) >= 2
    row1_hash = rows[0][0]
    row2_prev = rows[1][1]
    assert row2_prev == row1_hash, (
        f"chain 斷鏈：row2.prev_hash={row2_prev!r} != row1.row_hash={row1_hash!r}"
    )


def test_invalid_token_returns_401(running_server):
    """非法 token 應回 401，且不寫入任何資料。"""
    url = running_server["url"]
    db = running_server["db"]

    con = sqlite3.connect(str(db))
    count_before = con.execute("SELECT COUNT(*) FROM agent_heartbeat").fetchone()[0]
    con.close()

    status, body = _post(url, "agent_heartbeat", {
        "agent_id": "test", "ts": 1700000000, "task": "ping",
        "status": "ok", "model": "haiku",
    }, token="this-is-a-bad-token")

    assert status == 401, f"應回 401，實際：{status} {body}"

    con = sqlite3.connect(str(db))
    count_after = con.execute("SELECT COUNT(*) FROM agent_heartbeat").fetchone()[0]
    con.close()
    assert count_after == count_before, "非法 token 不應寫入任何資料"


def test_chain_passes_verify_chain(running_server):
    """寫入後，verify_chain.py --db --table 應 exit 0，且 failures 為空。"""
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "verify_chain.py"),
            "--db", str(running_server["db"]),
            "--table", "ohlcv",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.returncode == 0, (
        f"verify_chain 回傳 exit {result.returncode}：\n{result.stdout}\n{result.stderr}"
    )
    output = json.loads(result.stdout)
    assert output["payload"]["ok"] is True, f"verify_chain 驗證失敗：{output}"
    assert output["payload"]["failed_tables"] == [], (
        f"有失敗表：{output['payload']['failed_tables']}"
    )
