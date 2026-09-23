#!/usr/bin/env python3
"""
calendar_update.py — 高影響事件日曆管理工具。

用法：
    python scripts/calendar_update.py --precheck-4h
        → 供 Router precheck 用：未來 4 小時有 HIGH 事件 → RUN；否則 SKIP。
        → 若日曆檔不存在，輸出 RUN（要求 MACRO 建立日曆）。

    python scripts/calendar_update.py --write-events <events_json_path>
        → MACRO Agent 呼叫：將 LLM 產出的事件列表合併寫入 data/calendar/events.json。
        → events_json_path 是一個 JSON 陣列檔，每筆格式見下方 EVENT_SCHEMA。

    python scripts/calendar_update.py --init-empty
        → 建立空白日曆檔（已存在則不覆蓋）。

    python scripts/calendar_update.py --init-seed
        → 從 shared/calendar_seed.json 初始化日曆（已存在則不覆蓋）。
        → 用於首次部署或日曆遺失後的緊急恢復。

EVENT_SCHEMA（每筆）：
    {
        "event":    "FOMC Rate Decision",       # 事件名稱
        "ts_utc":   "2026-09-17T18:00:00Z",     # UTC ISO-8601
        "ts_taipei":"2026-09-18T02:00:00+08:00", # Taipei ISO-8601
        "impact":   "HIGH",                     # HIGH / MED / LOW
        "affects":  ["T4", "T1", "T3"]          # 影響的商品層
    }

安全原則：
    - 來源不可用時保留舊資料並告警；絕不清空已有事件。
    - precheck 找不到日曆檔 → 輸出 RUN（讓 MACRO 重建），不輸出 SKIP。
    - --write-events 收到空陣列 → 只保留舊資料、列印警告，不清空。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import td_console  # noqa: F401  (Windows cp950 主控台修正)

ROOT = Path(__file__).resolve().parents[1]
CALENDAR_PATH = ROOT / "data" / "calendar" / "events.json"
SEED_PATH = ROOT / "shared" / "calendar_seed.json"

UTC = timezone.utc
TAIPEI_OFFSET = timezone(timedelta(hours=8))
PRECHECK_WINDOW_HOURS = 4
REQUIRED_FIELDS = {"event", "ts_utc", "ts_taipei", "impact", "affects"}
VALID_IMPACT = {"HIGH", "MED", "LOW"}


# ---------------------------------------------------------------------------
# 通用工具
# ---------------------------------------------------------------------------

def _load_existing() -> list[dict]:
    """載入現有日曆；失敗時回傳空列表並印警告。"""
    if not CALENDAR_PATH.exists():
        return []
    try:
        data = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        print(f"WARNING: {CALENDAR_PATH} 格式不是陣列，視為空日曆", file=sys.stderr)
        return []
    except (json.JSONDecodeError, OSError) as e:
        print(f"WARNING: 無法讀取 {CALENDAR_PATH}：{e}", file=sys.stderr)
        return []


def _write_calendar(events: list[dict]) -> None:
    CALENDAR_PATH.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR_PATH.write_text(
        json.dumps(events, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _parse_ts(ts_str: str) -> datetime:
    """解析 ISO-8601（含 Z 或 +HH:MM），回傳有時區的 datetime。"""
    ts_str = ts_str.replace("Z", "+00:00")
    return datetime.fromisoformat(ts_str)


def _validate_event(e: dict) -> list[str]:
    errors = []
    missing = REQUIRED_FIELDS - e.keys()
    if missing:
        errors.append(f"缺少欄位：{missing}")
    if e.get("impact") not in VALID_IMPACT:
        errors.append(f"impact 無效：{e.get('impact')}")
    for ts_field in ("ts_utc", "ts_taipei"):
        try:
            _parse_ts(e.get(ts_field, ""))
        except (ValueError, TypeError):
            errors.append(f"{ts_field} 時間格式錯誤：{e.get(ts_field)}")
    if not isinstance(e.get("affects"), list):
        errors.append("affects 必須是陣列")
    return errors


# ---------------------------------------------------------------------------
# precheck-4h
# ---------------------------------------------------------------------------

def cmd_precheck_4h() -> int:
    """供 Router precheck 使用；輸出以 SKIP 開頭才不觸發 MACRO。"""
    if not CALENDAR_PATH.exists():
        print("RUN 日曆檔不存在，觸發 MACRO 更新日曆")
        return 0

    events = _load_existing()
    if not events:
        print("RUN 日曆為空，觸發 MACRO 更新日曆")
        return 0

    now_utc = datetime.now(UTC)
    window_end = now_utc + timedelta(hours=PRECHECK_WINDOW_HOURS)

    high_upcoming: list[str] = []
    for e in events:
        if e.get("impact") != "HIGH":
            continue
        try:
            ts = _parse_ts(e["ts_utc"]).astimezone(UTC)
        except (KeyError, ValueError):
            continue
        if now_utc <= ts <= window_end:
            high_upcoming.append(e.get("event", "未命名事件"))

    if high_upcoming:
        names = "、".join(high_upcoming)
        print(f"RUN HIGH 事件：{names}")
    else:
        print(f"SKIP 未來 {PRECHECK_WINDOW_HOURS} 小時無 HIGH 事件（共 {len(events)} 筆）")
    return 0


# ---------------------------------------------------------------------------
# write-events
# ---------------------------------------------------------------------------

def cmd_write_events(source_path_str: str) -> int:
    """MACRO Agent 提供 JSON 陣列，合併進 data/calendar/events.json。"""
    source_path = Path(source_path_str)
    if not source_path.exists():
        print(f"ERROR: 找不到事件來源檔：{source_path}", file=sys.stderr)
        return 1

    try:
        new_events: list[dict] = json.loads(source_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: 讀取事件來源失敗：{e}", file=sys.stderr)
        return 1

    if not isinstance(new_events, list):
        print("ERROR: 事件來源必須是 JSON 陣列", file=sys.stderr)
        return 1

    if not new_events:
        print("WARNING: 收到空陣列，保留現有日曆不更新", file=sys.stderr)
        existing = _load_existing()
        print(json.dumps({"kept": len(existing), "added": 0}, ensure_ascii=False))
        return 0

    # 驗證每筆
    valid_events, skipped = [], 0
    for i, e in enumerate(new_events):
        errs = _validate_event(e)
        if errs:
            print(f"WARNING: 第 {i} 筆驗證失敗（略過）：{errs}", file=sys.stderr)
            skipped += 1
        else:
            valid_events.append(e)

    if not valid_events:
        print("ERROR: 所有事件驗證失敗，保留現有日曆不更新", file=sys.stderr)
        return 1

    # 合併策略：以 (event, ts_utc) 為鍵去重，新事件覆蓋舊事件
    existing = _load_existing()
    merged: dict[tuple, dict] = {}
    for e in existing:
        key = (e.get("event", ""), e.get("ts_utc", ""))
        merged[key] = e
    for e in valid_events:
        key = (e.get("event", ""), e.get("ts_utc", ""))
        merged[key] = e

    # 只保留未來 60 天的事件（避免無限累積過期資料）
    now_utc = datetime.now(UTC)
    cutoff = now_utc + timedelta(days=60)
    retained = [
        e for e in merged.values()
        if _is_future(e, now_utc - timedelta(hours=1), cutoff)
    ]
    retained.sort(key=lambda e: e.get("ts_utc", ""))

    _write_calendar(retained)
    result = {"total": len(retained), "added_or_updated": len(valid_events), "skipped_invalid": skipped}
    print(json.dumps(result, ensure_ascii=False))
    return 0


def _is_future(e: dict, after: datetime, before: datetime) -> bool:
    try:
        ts = _parse_ts(e.get("ts_utc", "")).astimezone(UTC)
        return after <= ts <= before
    except (ValueError, TypeError):
        return True  # 解析不了就保留，不要丟掉可能有效的事件


# ---------------------------------------------------------------------------
# init-empty
# ---------------------------------------------------------------------------

def cmd_init_empty() -> int:
    """建立空白日曆檔（不覆蓋）。"""
    if CALENDAR_PATH.exists():
        print(f"SKIP {CALENDAR_PATH} 已存在，不覆蓋")
        return 0
    _write_calendar([])
    print(f"OK 已建立空白日曆：{CALENDAR_PATH}")
    return 0


def cmd_init_seed() -> int:
    """從 shared/calendar_seed.json 初始化日曆（不覆蓋現有）。"""
    if CALENDAR_PATH.exists():
        print(f"SKIP {CALENDAR_PATH} 已存在，不覆蓋")
        return 0
    if not SEED_PATH.exists():
        print(f"ERROR: seed 檔不存在：{SEED_PATH}", file=sys.stderr)
        return 1
    try:
        seed_events: list[dict] = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"ERROR: 讀取 seed 失敗：{e}", file=sys.stderr)
        return 1
    _write_calendar(seed_events)
    print(f"OK 已從 seed 初始化日曆（{len(seed_events)} 筆）：{CALENDAR_PATH}")
    return 0


# ---------------------------------------------------------------------------
# 入口
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] == "--precheck-4h":
        return cmd_precheck_4h()
    if args[0] == "--write-events":
        if len(args) < 2:
            print("ERROR: --write-events 需要一個路徑參數", file=sys.stderr)
            return 1
        return cmd_write_events(args[1])
    if args[0] == "--init-empty":
        return cmd_init_empty()
    if args[0] == "--init-seed":
        return cmd_init_seed()
    print(f"ERROR: 未知參數 {args[0]}（用 --precheck-4h / --write-events <path> / --init-empty / --init-seed）", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
