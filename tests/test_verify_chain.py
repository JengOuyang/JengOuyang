"""verify_chain.py 的單元測試。`python -m pytest tests/test_verify_chain.py -q`"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_chain as vc


def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


# ---------- 工具函數 ----------

class TestSha256Hex:
    def test_known_value(self):
        assert vc.sha256_hex("abc") == sha256("abc")


class TestCanonicalJson:
    def test_sorts_keys(self):
        assert vc.canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'

    def test_no_spaces(self):
        result = vc.canonical_json({"x": 1})
        assert " " not in result

    def test_none_becomes_null(self):
        assert vc.canonical_json({"v": None}) == '{"v":null}'


# ---------- DB 測試輔助 ----------

def _make_test_db(path: Path, rows: list[tuple]) -> sqlite3.Connection:
    """建立帶 biz_col 的測試表，rows = [(biz_val, prev_hash, row_hash), ...]"""
    conn = sqlite3.connect(str(path))
    conn.execute(
        "CREATE TABLE t (row_id INTEGER PRIMARY KEY, biz_col TEXT,"
        " ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT)"
    )
    for i, (biz_val, prev_h, row_h) in enumerate(rows, start=1):
        conn.execute(
            "INSERT INTO t VALUES (?,?,0,'test',?,?)",
            (i, biz_val, prev_h, row_h),
        )
    conn.commit()
    return conn


def _correct_hash(prev: str, biz_val) -> str:
    return sha256(prev + canonical({"biz_col": biz_val}))


# ---------- verify_table ----------

class TestVerifyTable:
    def test_empty_table_ok(self, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "db.db"))
        conn.execute(
            "CREATE TABLE t (row_id INTEGER PRIMARY KEY, biz_col TEXT,"
            " ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT)"
        )
        conn.commit()
        result = vc.verify_table(conn, "t")
        assert result["ok"] is True
        assert result["rows_checked"] == 0

    def test_missing_table_returns_ok(self, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "db.db"))
        result = vc.verify_table(conn, "nonexistent")
        assert result["ok"] is True

    def test_valid_chain_passes(self, tmp_path):
        h1 = _correct_hash("", "alpha")
        h2 = _correct_hash(h1, "beta")
        conn = _make_test_db(tmp_path / "db.db", [
            ("alpha", "", h1),
            ("beta", h1, h2),
        ])
        result = vc.verify_table(conn, "t")
        assert result["ok"] is True
        assert result["rows_checked"] == 2
        assert result["failures"] == []

    def test_tampered_hash_fails(self, tmp_path):
        h1 = _correct_hash("", "alpha")
        bad_hash = "0" * 64  # 偽造的 hash
        conn = _make_test_db(tmp_path / "db.db", [
            ("alpha", "", bad_hash),
        ])
        result = vc.verify_table(conn, "t")
        assert result["ok"] is False
        assert len(result["failures"]) >= 1
        assert result["failures"][0]["hash_ok"] is False

    def test_broken_chain_fails(self, tmp_path):
        h1 = _correct_hash("", "alpha")
        # row 2 的 prev_hash 故意填錯（不等於 row 1 的 row_hash）
        wrong_prev = "a" * 64
        h2 = _correct_hash(wrong_prev, "beta")
        conn = _make_test_db(tmp_path / "db.db", [
            ("alpha", "", h1),
            ("beta", wrong_prev, h2),   # hash 本身正確，但 chain 斷了
        ])
        result = vc.verify_table(conn, "t")
        assert result["ok"] is False
        assert result["failures"][0]["chain_ok"] is False

    def test_failures_truncated_at_10(self, tmp_path):
        rows = [("v", "", "bad" * 21)] * 20  # 20 列全錯
        conn = _make_test_db(tmp_path / "db.db", rows)
        result = vc.verify_table(conn, "t")
        assert result["ok"] is False
        # 最多 10 筆 + truncated note
        assert any("truncated" in str(f) for f in result["failures"])


# ---------- main() ----------

class TestMain:
    def test_missing_db_exits_1(self, tmp_path, monkeypatch):
        monkeypatch.setattr(vc, "DB_PATH", tmp_path / "no.db")
        monkeypatch.setattr(sys, "argv", ["verify_chain.py"])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vc.main()
        assert rc == 1
        assert "error" in json.loads(buf.getvalue())

    def test_all_empty_tables_exits_0(self, tmp_path, monkeypatch):
        db = tmp_path / "tradedesk.db"
        conn = sqlite3.connect(str(db))
        for tbl in vc.TABLES:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {tbl} "
                "(row_id INTEGER PRIMARY KEY, ingest_ts INTEGER,"
                " writer TEXT, prev_hash TEXT, row_hash TEXT)"
            )
        conn.commit()
        conn.close()
        monkeypatch.setattr(vc, "DB_PATH", db)
        monkeypatch.setattr(sys, "argv", ["verify_chain.py"])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vc.main()
        assert rc == 0
        out = json.loads(buf.getvalue())
        assert out["payload"]["ok"] is True
        assert out["msg_type"] == "AUDIT_ANCHOR"

    def test_table_flag(self, tmp_path, monkeypatch):
        db = tmp_path / "tradedesk.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE ohlcv (row_id INTEGER PRIMARY KEY,"
            " ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT)"
        )
        conn.commit()
        conn.close()
        monkeypatch.setattr(vc, "DB_PATH", db)
        monkeypatch.setattr(sys, "argv", ["verify_chain.py", "--table", "ohlcv"])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vc.main()
        assert rc == 0
        out = json.loads(buf.getvalue())
        assert out["payload"]["tables_checked"] == 1

    def test_bad_data_exits_1_and_data_alert(self, tmp_path, monkeypatch):
        db = tmp_path / "tradedesk.db"
        conn = sqlite3.connect(str(db))
        conn.execute(
            "CREATE TABLE ohlcv (row_id INTEGER PRIMARY KEY, symbol TEXT,"
            " ingest_ts INTEGER, writer TEXT, prev_hash TEXT, row_hash TEXT)"
        )
        conn.execute(
            "INSERT INTO ohlcv VALUES (1,'BTC',0,'test','','bad_hash')"
        )
        conn.commit()
        conn.close()
        monkeypatch.setattr(vc, "DB_PATH", db)
        monkeypatch.setattr(sys, "argv", ["verify_chain.py", "--table", "ohlcv"])
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = vc.main()
        assert rc == 1
        out = json.loads(buf.getvalue())
        assert out["msg_type"] == "DATA_ALERT"
        assert out["payload"]["ok"] is False
