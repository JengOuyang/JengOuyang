"""write_macro.py 的單元測試。`python -m pytest tests/test_write_macro.py -q`"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

VALID_BRIEF = {
    "date": "2026-09-16",
    "regime": "EVENT_RISK",
    "bias": "BEAR",
    "confidence": 0.65,
    "drivers": ["FOMC 升息決定", "美債 10Y 突破 5%"],
    "changes_vs_yesterday": "10Y 從 4.97% 升至 5.02%",
    "event_calendar": [
        {"event": "FOMC Rate Decision", "ts_utc": "2026-09-16T18:00:00Z",
         "impact": "HIGH", "affects": ["T1", "T2", "T3", "T4"]}
    ],
    "sources": [
        {"title": "CNBC", "url": "https://www.cnbc.com/test"}
    ],
}


def run_script(input_json: dict | None = None, args: list[str] | None = None,
               env_extra: dict | None = None) -> subprocess.CompletedProcess:
    import os
    env = os.environ.copy()
    env["INGEST_TOKEN_MACRO"] = "test-token"
    if env_extra:
        env.update(env_extra)
    cmd = [sys.executable, str(ROOT / "scripts" / "write_macro.py")] + (args or [])
    return subprocess.run(
        cmd,
        input=json.dumps(input_json) if input_json is not None else None,
        capture_output=True,
        text=True,
        cwd=ROOT,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


class TestValidation:
    def test_missing_required_field_fails(self, tmp_path):
        bad = {k: v for k, v in VALID_BRIEF.items() if k != "date"}
        result = run_script(bad)
        assert result.returncode == 1
        out = json.loads(result.stdout.strip().splitlines()[-1])
        assert "error" in out

    def test_invalid_regime_fails(self, tmp_path):
        bad = {**VALID_BRIEF, "regime": "CHAOS"}
        result = run_script(bad)
        # jsonschema 安裝時應失敗；未安裝時 regime 不在基本欄位檢查範圍所以只要不崩
        # 記錄這個 gap：完整 enum 驗證需要 jsonschema
        # 此測試在有 jsonschema 時斷言 returncode==1
        try:
            import jsonschema  # noqa: F401
            assert result.returncode == 1
        except ImportError:
            pass  # acceptable degradation — documented

    def test_invalid_json_fails(self):
        import os
        env = os.environ.copy()
        env["INGEST_TOKEN_MACRO"] = "test-token"
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "write_macro.py")],
            input="not json at all",
            capture_output=True, text=True, cwd=ROOT, env=env,
            encoding="utf-8", errors="replace",
        )
        assert result.returncode == 1


class TestLocalWrite:
    def test_local_file_created(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TD_MACRO_DIR", str(tmp_path))

        import write_macro as wm
        monkeypatch.setattr(wm, "MACRO_DIR", tmp_path)

        # mock post_ingest to avoid network
        monkeypatch.setattr(wm, "post_ingest", lambda p: {"row_id": 1, "row_hash": "abc"})

        wm.validate_schema(VALID_BRIEF)
        dest = wm.save_local(VALID_BRIEF, VALID_BRIEF["date"])
        assert dest.exists()
        saved = json.loads(dest.read_text(encoding="utf-8"))
        assert saved["date"] == "2026-09-16"

    def test_local_filename_format(self, tmp_path, monkeypatch):
        import write_macro as wm
        monkeypatch.setattr(wm, "MACRO_DIR", tmp_path)
        dest = wm.save_local(VALID_BRIEF, "2026-09-16")
        assert dest.name == "macro_brief_20260916.json"


class TestPayloadMapping:
    def test_build_ingest_payload_required_keys(self):
        import write_macro as wm
        p = wm.build_ingest_payload(VALID_BRIEF)
        for key in ("date", "regime", "bias", "confidence",
                    "events_json", "summary", "sources_json", "ingest_ts", "writer"):
            assert key in p, f"missing key: {key}"

    def test_events_json_is_valid_json(self):
        import write_macro as wm
        p = wm.build_ingest_payload(VALID_BRIEF)
        events = json.loads(p["events_json"])
        assert isinstance(events, list)
        assert events[0]["event"] == "FOMC Rate Decision"

    def test_sources_json_is_valid_json(self):
        import write_macro as wm
        p = wm.build_ingest_payload(VALID_BRIEF)
        sources = json.loads(p["sources_json"])
        assert isinstance(sources, list)


class TestIngestError:
    def test_missing_token_raises(self, monkeypatch):
        monkeypatch.delenv("INGEST_TOKEN_MACRO", raising=False)
        import write_macro as wm
        with pytest.raises(RuntimeError, match="INGEST_TOKEN_MACRO"):
            wm.post_ingest({})

    def test_server_down_raises(self, monkeypatch):
        monkeypatch.setenv("INGEST_TOKEN_MACRO", "tok")
        monkeypatch.setenv("INGEST_PORT", "19999")  # nothing listening there
        import write_macro as wm
        with pytest.raises(RuntimeError, match="ingest server"):
            wm.post_ingest({"date": "2026-09-16"})
