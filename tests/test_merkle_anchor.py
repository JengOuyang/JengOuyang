"""merkle_anchor.py 的單元測試。`python -m pytest tests/test_merkle_anchor.py -q`"""
from __future__ import annotations

import datetime as dt
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import merkle_anchor as ma


class TestMerkleRoot:
    def test_empty_returns_zeros(self):
        assert ma.merkle_root([]) == "0" * 64

    def test_single_hash(self):
        h = "a" * 64
        assert ma.merkle_root([h]) == h

    def test_two_hashes(self):
        h1, h2 = "a" * 64, "b" * 64
        expected = ma.sha256_hex(h1 + h2)
        assert ma.merkle_root([h1, h2]) == expected

    def test_odd_count_duplicates_last(self):
        h1, h2, h3 = "a" * 64, "b" * 64, "c" * 64
        # layer 1: sha(h1+h2), sha(h3+h3)
        l1 = ma.sha256_hex(h1 + h2)
        l2 = ma.sha256_hex(h3 + h3)
        assert ma.merkle_root([h1, h2, h3]) == ma.sha256_hex(l1 + l2)

    def test_four_hashes(self):
        hs = ["a" * 64, "b" * 64, "c" * 64, "d" * 64]
        l1 = ma.sha256_hex(hs[0] + hs[1])
        l2 = ma.sha256_hex(hs[2] + hs[3])
        assert ma.merkle_root(hs) == ma.sha256_hex(l1 + l2)


class TestDayTsRange:
    def test_known_date(self):
        start, end = ma.day_ts_range("2026-09-22")
        assert end - start == 86400
        d = dt.datetime.fromtimestamp(start, tz=dt.timezone.utc)
        assert d.date().isoformat() == "2026-09-22"
        assert d.hour == 0 and d.minute == 0


class TestQueryTable:
    def test_missing_table_returns_zero(self, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "empty.db"))
        count, hashes = ma.query_table(conn, "nonexistent", 0, 9999999999)
        assert count == 0 and hashes == []
        conn.close()

    def test_filters_by_ingest_ts(self, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "test.db"))
        conn.execute(
            "CREATE TABLE t (row_id INTEGER PRIMARY KEY, ingest_ts INTEGER,"
            " row_hash TEXT)"
        )
        conn.execute("INSERT INTO t VALUES (1, 100, 'hash_a')")
        conn.execute("INSERT INTO t VALUES (2, 200, 'hash_b')")
        conn.execute("INSERT INTO t VALUES (3, 300, 'hash_c')")
        conn.commit()
        count, hashes = ma.query_table(conn, "t", 100, 200)
        assert count == 1
        assert hashes == ["hash_a"]
        conn.close()


def _make_db(path: Path) -> None:
    conn = sqlite3.connect(str(path))
    for tbl in ma.TABLES:
        conn.execute(
            f"CREATE TABLE IF NOT EXISTS {tbl} "
            "(row_id INTEGER PRIMARY KEY, ingest_ts INTEGER, row_hash TEXT)"
        )
    conn.commit()
    conn.close()


def run_script(args: list[str], env_extra: dict | None = None) -> subprocess.CompletedProcess:
    import os
    env = os.environ.copy()
    env["INGEST_TOKEN_LEDGER"] = "test-token"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "merkle_anchor.py")] + args,
        capture_output=True, text=True, cwd=ROOT, env=env,
        encoding="utf-8", errors="replace",
    )


class TestMainScript:
    def test_missing_db_exits_1(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ma, "DB_PATH", tmp_path / "no.db")
        monkeypatch.setattr(
            sys, "argv", ["merkle_anchor.py", "--dry-run", "--date", "2026-09-22"]
        )
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ma.main()
        assert rc == 1
        out = json.loads(buf.getvalue())
        assert "error" in out

    def test_dry_run_outputs_audit_anchor(self, tmp_path, monkeypatch):
        db = tmp_path / "tradedesk.db"
        _make_db(db)
        monkeypatch.setattr(ma, "DB_PATH", db)
        # patch sys.argv
        monkeypatch.setattr(
            sys, "argv", ["merkle_anchor.py", "--dry-run", "--date", "2026-09-22"]
        )
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ma.main()
        assert rc == 0
        out = json.loads(buf.getvalue())
        assert out["msg_type"] == "AUDIT_ANCHOR"
        assert out["payload"]["date"] == "2026-09-22"
        assert out["payload"]["dry_run"] is True
        assert out["payload"]["errors"] == []
        # 空庫所有表 row_count 為 0
        assert all(v == 0 for v in out["payload"]["row_counts"].values())

    def test_dry_run_no_ingest_token_needed(self, tmp_path, monkeypatch):
        db = tmp_path / "tradedesk.db"
        _make_db(db)
        monkeypatch.setattr(ma, "DB_PATH", db)
        monkeypatch.setattr(
            sys, "argv", ["merkle_anchor.py", "--dry-run", "--date", "2026-09-22"]
        )
        monkeypatch.delenv("INGEST_TOKEN_LEDGER", raising=False)
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ma.main()
        # dry-run 不需要 token，應該成功
        assert rc == 0

    def test_missing_token_exits_1(self, tmp_path, monkeypatch):
        db = tmp_path / "tradedesk.db"
        _make_db(db)
        monkeypatch.setattr(ma, "DB_PATH", db)
        monkeypatch.setattr(
            sys, "argv", ["merkle_anchor.py", "--date", "2026-09-22"]
        )
        monkeypatch.delenv("INGEST_TOKEN_LEDGER", raising=False)
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ma.main()
        assert rc == 1
        out = json.loads(buf.getvalue())
        assert "INGEST_TOKEN_LEDGER" in out["error"]
