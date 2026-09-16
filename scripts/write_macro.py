#!/usr/bin/env python3
"""
write_macro.py — 將每日 MACRO_BRIEF JSON 寫入本地備份並透過 LEDGER ingest 入倉。

用法（MACRO Agent 在自己的目錄下執行）：
    python ../../scripts/write_macro.py < outbox/macro_brief_YYYYMMDD.json
    或
    python ../../scripts/write_macro.py outbox/macro_brief_YYYYMMDD.json

輸入：符合 shared/schemas/macro_brief.schema.json 的 JSON。
輸出：
  1. data/macro/macro_brief_YYYYMMDD.json（本地備份）
  2. POST http://127.0.0.1:8787/ingest/macro_brief（LEDGER ingest）

環境變數：
  INGEST_TOKEN_MACRO  — 寫入 token（必填）
  INGEST_PORT         — ingest server port（預設 8787）
  TD_DB               — 資料庫路徑（僅供 fallback 直寫，正常走 HTTP）
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import td_console  # noqa: F401  (Windows cp950 console fix)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "shared" / "schemas" / "macro_brief.schema.json"
MACRO_DIR = ROOT / "data" / "macro"


def load_input() -> dict:
    if len(sys.argv) >= 2:
        raw = Path(sys.argv[1]).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    return json.loads(raw)


def validate_schema(data: dict) -> None:
    try:
        import jsonschema
    except ImportError:
        # jsonschema 未安裝時只做基本欄位檢查
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        required = schema.get("required", [])
        missing = [f for f in required if f not in data]
        if missing:
            raise ValueError(f"缺少必填欄位：{', '.join(missing)}")
        return

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(data, schema)


def save_local(data: dict, date_str: str) -> Path:
    MACRO_DIR.mkdir(parents=True, exist_ok=True)
    dest = MACRO_DIR / f"macro_brief_{date_str.replace('-', '')}.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def post_ingest(payload: dict) -> dict:
    token = os.environ.get("INGEST_TOKEN_MACRO", "")
    if not token:
        raise RuntimeError(
            "INGEST_TOKEN_MACRO 未設定；請在 router/.env 補上後重試"
        )
    port = os.environ.get("INGEST_PORT", "8787")
    url = f"http://127.0.0.1:{port}/ingest/macro_brief"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "X-Writer-Token": token,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LEDGER ingest 失敗 HTTP {e.code}: {detail}") from e
    except OSError as e:
        raise RuntimeError(
            f"無法連接 LEDGER ingest server（{url}）：{e}\n"
            "請確認 engine/ingest_server.py 正在執行。"
        ) from e


def build_ingest_payload(data: dict) -> dict:
    """將 macro_brief schema 欄位對應到 macro_brief 資料表欄位。"""
    return {
        "date": data["date"],
        "regime": data["regime"],
        "bias": data["bias"],
        "confidence": data["confidence"],
        "events_json": json.dumps(data.get("event_calendar", []), ensure_ascii=False),
        "summary": json.dumps(
            {
                "drivers": data.get("drivers", []),
                "changes_vs_yesterday": data.get("changes_vs_yesterday", ""),
                "asset_notes": data.get("asset_notes", {}),
                "crypto_flows": data.get("crypto_flows", {}),
                "confidence_note": data.get("confidence_note", ""),
                "data_gaps": data.get("data_gaps", []),
            },
            ensure_ascii=False,
        ),
        "sources_json": json.dumps(data.get("sources", []), ensure_ascii=False),
        "model": data.get("model", "unknown"),
        "ingest_ts": int(time.time()),
        "writer": "write_macro",
    }


def main() -> int:
    try:
        data = load_input()
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"error": f"讀取輸入失敗：{e}"}, ensure_ascii=False))
        return 1

    try:
        validate_schema(data)
    except Exception as e:
        print(json.dumps({"error": f"Schema 驗證失敗：{e}"}, ensure_ascii=False))
        return 1

    date_str = data["date"]

    # 1. 本地備份
    try:
        dest = save_local(data, date_str)
        print(json.dumps({"local": str(dest)}, ensure_ascii=False))
    except OSError as e:
        print(json.dumps({"error": f"本地寫入失敗：{e}"}, ensure_ascii=False))
        return 1

    # 2. LEDGER ingest
    try:
        payload = build_ingest_payload(data)
        result = post_ingest(payload)
        print(json.dumps({"ingest": result}, ensure_ascii=False))
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
